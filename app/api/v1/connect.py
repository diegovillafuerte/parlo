"""WhatsApp Business connection endpoints for onboarding.

These endpoints handle the Meta Embedded Signup flow where business owners
connect their WhatsApp Business account during onboarding.

Flow:
1. AI sends user a connect URL with token: /connect?token=xxx
2. User opens URL in browser, sees connect page
3. Frontend calls GET /api/v1/connect/session?token=xxx to get session info
4. User clicks "Connect with Facebook" → Meta Embedded Signup
5. Frontend receives credentials from Meta (via message event)
6. Frontend calls POST /api/v1/connect/complete with authorization code + IDs
7. Backend exchanges code for long-lived access token via Meta API
8. Backend registers webhook with Meta to receive messages
9. Backend creates Organization and marks onboarding complete
10. Frontend shows success and deep-links back to WhatsApp
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.config import get_settings
from app.models import (
    Location,
    OnboardingSession,
    OnboardingState,
    Organization,
    OrganizationStatus,
    ServiceType,
    Spot,
    Staff,
    StaffRole,
)

router = APIRouter(prefix="/connect", tags=["connect"])
logger = logging.getLogger(__name__)
settings = get_settings()

# Default business hours
DEFAULT_BUSINESS_HOURS = {
    "monday": {"open": "09:00", "close": "19:00"},
    "tuesday": {"open": "09:00", "close": "19:00"},
    "wednesday": {"open": "09:00", "close": "19:00"},
    "thursday": {"open": "09:00", "close": "19:00"},
    "friday": {"open": "09:00", "close": "19:00"},
    "saturday": {"open": "09:00", "close": "17:00"},
    "sunday": {"closed": True},
}


class SessionInfoResponse(BaseModel):
    """Response with onboarding session info for connect page."""

    session_id: str
    business_name: str
    owner_name: str | None
    services: list[dict]
    state: str


class WhatsAppConnectRequest(BaseModel):
    """Request to complete WhatsApp Business connection."""

    token: str
    phone_number_id: str | None = None  # Meta's phone number ID (from session info event)
    waba_id: str | None = None  # WhatsApp Business Account ID (from session info event)
    code: str  # Authorization code to exchange for access token


async def exchange_code_for_token(code: str) -> dict[str, str]:
    """Exchange authorization code for long-lived access token.

    Meta's OAuth flow:
    1. Exchange authorization code for short-lived user access token
    2. Exchange short-lived token for long-lived token (60 days)

    Args:
        code: Authorization code from Meta Embedded Signup

    Returns:
        Dict with access_token and token_type

    Raises:
        HTTPException: If token exchange fails
    """
    if not settings.meta_app_id or not settings.meta_app_secret:
        logger.warning("Meta App credentials not configured, skipping token exchange")
        # Return the code as-is if credentials not configured (for testing)
        return {"access_token": code, "token_type": "bearer"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Exchange code for short-lived access token
        token_url = "https://graph.facebook.com/v18.0/oauth/access_token"
        token_params = {
            "client_id": settings.meta_app_id,
            "client_secret": settings.meta_app_secret,
            "code": code,
            # Redirect URI must match what was used in the OAuth flow
            "redirect_uri": f"{settings.frontend_url}/connect",
        }

        try:
            response = await client.get(token_url, params=token_params)
            response.raise_for_status()
            token_data = response.json()

            short_lived_token = token_data.get("access_token")
            if not short_lived_token:
                logger.error(f"No access_token in response: {token_data}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Error obteniendo token de acceso de Meta",
                )

            logger.info("Successfully exchanged code for short-lived token")

        except httpx.HTTPError as e:
            logger.error(f"Failed to exchange code for token: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Error conectando con Meta. Por favor intenta de nuevo.",
            )

        # Step 2: Exchange short-lived token for long-lived token
        long_lived_url = "https://graph.facebook.com/v18.0/oauth/access_token"
        long_lived_params = {
            "grant_type": "fb_exchange_token",
            "client_id": settings.meta_app_id,
            "client_secret": settings.meta_app_secret,
            "fb_exchange_token": short_lived_token,
        }

        try:
            response = await client.get(long_lived_url, params=long_lived_params)
            response.raise_for_status()
            long_lived_data = response.json()

            access_token = long_lived_data.get("access_token")
            if not access_token:
                logger.error(f"No access_token in long-lived response: {long_lived_data}")
                # Fall back to short-lived token
                access_token = short_lived_token

            logger.info("Successfully exchanged for long-lived token")
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": long_lived_data.get("expires_in", 5184000),  # 60 days default
            }

        except httpx.HTTPError as e:
            logger.warning(f"Failed to get long-lived token, using short-lived: {e}")
            # Fall back to short-lived token if long-lived exchange fails
            return {
                "access_token": short_lived_token,
                "token_type": "bearer",
            }


async def register_webhook_with_meta(waba_id: str, access_token: str) -> bool:
    """Subscribe the app to receive webhooks for this WABA.

    After a business connects via Embedded Signup, we need to subscribe
    our app to receive webhook events (messages) for their WABA.

    Args:
        waba_id: WhatsApp Business Account ID
        access_token: Business's long-lived access token

    Returns:
        True if subscription succeeded
    """
    if not waba_id or not access_token:
        logger.warning("Cannot register webhook: missing waba_id or access_token")
        return False

    # The webhook URL must be configured in Meta App Dashboard
    # This call just subscribes the app to receive events for this WABA
    url = f"https://graph.facebook.com/v18.0/{waba_id}/subscribed_apps"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                url,
                headers={"Authorization": f"Bearer {access_token}"},
                # Subscribe to messages field
                data={"subscribed_fields": "messages"},
            )
            response.raise_for_status()
            result = response.json()

            if result.get("success"):
                logger.info(f"✅ Successfully registered webhook for WABA {waba_id}")
                return True
            else:
                logger.warning(f"⚠️  Webhook registration returned: {result}")
                return False

        except httpx.HTTPError as e:
            logger.error(f"❌ Failed to register webhook for WABA {waba_id}: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"   Response: {e.response.text}")
            return False


async def validate_whatsapp_credentials(
    phone_number_id: str,
    waba_id: str,
    access_token: str,
) -> bool:
    """Validate WhatsApp credentials by making a test API call.

    Args:
        phone_number_id: Meta's phone number ID
        waba_id: WhatsApp Business Account ID
        access_token: Access token to validate

    Returns:
        True if credentials are valid
    """
    if not phone_number_id or not waba_id:
        logger.warning("Missing phone_number_id or waba_id, skipping validation")
        return True  # Allow completion without validation for now

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Try to fetch phone number details to validate credentials
        url = f"https://graph.facebook.com/v18.0/{phone_number_id}"
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Validated WhatsApp credentials for phone: {data.get('display_phone_number', 'unknown')}")
            return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to validate WhatsApp credentials: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return False


class ConnectCompleteResponse(BaseModel):
    """Response after completing connection."""

    success: bool
    organization_id: str
    business_name: str
    dashboard_url: str
    message: str


@router.get("/session", response_model=SessionInfoResponse)
async def get_session_by_token(
    token: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SessionInfoResponse:
    """Get onboarding session info for connection page.

    Args:
        token: Connection token from URL
        db: Database session

    Returns:
        Session info including business name and services
    """
    result = await db.execute(
        select(OnboardingSession).where(
            OnboardingSession.connection_token == token,
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sesión no encontrada o token inválido",
        )

    # Check if session is in valid state for connection
    if session.state == OnboardingState.COMPLETED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta cuenta ya fue configurada",
        )

    if session.state == OnboardingState.ABANDONED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta sesión fue abandonada. Por favor inicia de nuevo.",
        )

    collected = session.collected_data or {}

    return SessionInfoResponse(
        session_id=str(session.id),
        business_name=collected.get("business_name", "Sin nombre"),
        owner_name=collected.get("owner_name") or session.owner_name,
        services=collected.get("services", []),
        state=session.state,
    )


@router.post("/complete", response_model=ConnectCompleteResponse)
async def complete_whatsapp_connection(
    data: WhatsAppConnectRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConnectCompleteResponse:
    """Complete WhatsApp Business connection and create organization.

    This is called by the frontend after the user completes Meta Embedded Signup.
    The authorization code is exchanged for a long-lived access token.

    Args:
        data: WhatsApp credentials from Meta (includes authorization code)
        db: Database session

    Returns:
        Success response with organization info
    """
    # Find session by token
    result = await db.execute(
        select(OnboardingSession).where(
            OnboardingSession.connection_token == data.token,
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sesión no encontrada",
        )

    if session.state == OnboardingState.COMPLETED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta cuenta ya fue configurada",
        )

    collected = session.collected_data or {}

    # Validate required data
    if not collected.get("business_name"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Falta el nombre del negocio",
        )

    if not collected.get("services"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Falta al menos un servicio",
        )

    # Exchange authorization code for long-lived access token
    logger.info(f"Exchanging authorization code for session {session.id}")
    token_data = await exchange_code_for_token(data.code)
    access_token = token_data["access_token"]

    # Validate WhatsApp credentials if we have them
    if data.phone_number_id and data.waba_id:
        is_valid = await validate_whatsapp_credentials(
            data.phone_number_id,
            data.waba_id,
            access_token,
        )
        if not is_valid:
            logger.warning(f"WhatsApp credential validation failed for session {session.id}")
            # Continue anyway - credentials might still work

    # Register webhook with Meta to receive messages for this WABA
    if data.waba_id:
        webhook_registered = await register_webhook_with_meta(data.waba_id, access_token)
        if not webhook_registered:
            logger.warning(
                f"⚠️  Webhook registration failed for WABA {data.waba_id}. "
                f"Messages may not be received. Manual retry may be needed."
            )
            # Continue anyway - org can still be created, webhook can be retried later

    # Calculate token expiry (60 days from now)
    token_expires_at = datetime.now(timezone.utc) + timedelta(days=60)

    # Store WhatsApp credentials in session
    session.whatsapp_phone_number_id = data.phone_number_id
    session.whatsapp_waba_id = data.waba_id
    session.whatsapp_access_token = access_token

    try:
        # Create organization and related entities
        org = await _create_organization_from_session(db, session, token_expires_at)

        # Mark session as completed
        session.state = OnboardingState.COMPLETED.value
        session.organization_id = str(org.id)

        await db.commit()

        logger.info(f"Organization created via WhatsApp connect: {org.id} - {org.name}")

        # Use configured frontend URL for dashboard
        dashboard_url = f"{settings.frontend_url}/login"

        return ConnectCompleteResponse(
            success=True,
            organization_id=str(org.id),
            business_name=org.name,
            dashboard_url=dashboard_url,
            message="¡Tu cuenta está lista!",
        )

    except Exception as e:
        logger.error(f"Error creating organization: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creando la cuenta: {str(e)}",
        )


async def _create_organization_from_session(
    db: AsyncSession,
    session: OnboardingSession,
    token_expires_at: datetime | None = None,
) -> Organization:
    """Create organization and all related entities from onboarding session.

    Args:
        db: Database session
        session: Onboarding session with collected data
        token_expires_at: When the WhatsApp access token expires (optional)

    Returns:
        Created organization
    """
    collected = session.collected_data

    # Extract country code
    phone = session.phone_number
    if phone.startswith("+"):
        phone = phone[1:]
    country_code = "52" if phone.startswith("52") else ("1" if phone.startswith("1") else "52")

    # 1. Create Organization with WhatsApp credentials
    org = Organization(
        name=collected["business_name"],
        phone_country_code=country_code,
        phone_number=session.phone_number,
        whatsapp_phone_number_id=session.whatsapp_phone_number_id,
        whatsapp_waba_id=session.whatsapp_waba_id,
        timezone="America/Mexico_City",
        status=OrganizationStatus.ACTIVE.value,
        settings={
            "language": "es",
            "currency": "MXN",
            "business_type": collected.get("business_type", "salon"),
            "whatsapp_access_token": session.whatsapp_access_token,  # Store token in settings
            "whatsapp_token_expires_at": token_expires_at.isoformat() if token_expires_at else None,
        },
    )
    db.add(org)
    await db.flush()
    await db.refresh(org)

    # 2. Create Location
    location = Location(
        organization_id=org.id,
        name="Principal",
        address=collected.get("address", ""),
        business_hours=collected.get("business_hours", DEFAULT_BUSINESS_HOURS),
        is_primary=True,
    )
    db.add(location)
    await db.flush()
    await db.refresh(location)

    # 3. Create Services
    services = []
    for svc_data in collected.get("services", []):
        price_cents = int(svc_data["price"] * 100)
        service = ServiceType(
            organization_id=org.id,
            name=svc_data["name"],
            duration_minutes=svc_data["duration_minutes"],
            price_cents=price_cents,
            is_active=True,
        )
        db.add(service)
        services.append(service)

    await db.flush()
    for svc in services:
        await db.refresh(svc)

    # 4. Create default Spot
    spot = Spot(
        organization_id=org.id,
        location_id=location.id,
        name="Estación 1",
        is_active=True,
    )
    db.add(spot)
    await db.flush()
    await db.refresh(spot)
    spot.service_types.extend(services)

    # 5. Create Staff (owner)
    owner_name = collected.get("owner_name") or session.owner_name or "Dueño"
    staff = Staff(
        organization_id=org.id,
        location_id=location.id,
        default_spot_id=spot.id,
        name=owner_name,
        phone_number=session.phone_number,
        role=StaffRole.OWNER.value,
        is_active=True,
        permissions={"can_manage_all": True},
    )
    db.add(staff)
    await db.flush()
    await db.refresh(staff)
    staff.service_types.extend(services)

    return org

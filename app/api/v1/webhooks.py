"""WhatsApp webhook endpoints - receive messages from Twilio and Meta Cloud API."""

import hashlib
import hmac
import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.config import get_settings
from app.services.message_router import MessageRouter
from app.services.whatsapp import WhatsAppClient

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)
settings = get_settings()


def _extract_phone_number(twilio_number: str) -> str:
    """Extract phone number from Twilio format.

    Args:
        twilio_number: Number in format 'whatsapp:+14155238886'

    Returns:
        Phone number with + prefix (e.g., '+14155238886')
    """
    # Remove 'whatsapp:' prefix if present
    if twilio_number.startswith("whatsapp:"):
        phone = twilio_number[9:]
    else:
        phone = twilio_number

    # Fix URL encoding issue: spaces should be +
    # In form data, + is decoded as space, so convert back
    phone = phone.strip()
    if phone and not phone.startswith("+"):
        phone = f"+{phone}"

    return phone


@router.post("/whatsapp", status_code=status.HTTP_200_OK)
async def receive_twilio_webhook(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    MessageSid: Annotated[str, Form()],
    From: Annotated[str, Form()],
    To: Annotated[str, Form()],
    Body: Annotated[str, Form()],
    ProfileName: Annotated[str | None, Form()] = None,
    NumMedia: Annotated[str | None, Form()] = None,
) -> PlainTextResponse:
    """Receive incoming WhatsApp messages from Twilio.

    Twilio sends webhook data as form-encoded POST.

    Args:
        MessageSid: Unique message identifier
        From: Sender number (format: whatsapp:+14155238886)
        To: Recipient number (our Twilio number)
        Body: Message content
        ProfileName: Sender's WhatsApp profile name
        NumMedia: Number of media attachments

    Returns:
        Empty TwiML response (or with reply message)
    """
    logger.info(
        f"\n{'='*80}\n"
        f"📬 TWILIO WEBHOOK RECEIVED\n"
        f"{'='*80}\n"
        f"  MessageSid: {MessageSid}\n"
        f"  From: {From}\n"
        f"  To: {To}\n"
        f"  Body: {Body}\n"
        f"  ProfileName: {ProfileName}\n"
        f"{'='*80}"
    )

    try:
        # Extract phone numbers
        sender_phone = _extract_phone_number(From)
        our_number = _extract_phone_number(To)

        # Skip media-only messages for now
        if NumMedia and int(NumMedia) > 0 and not Body:
            logger.info(f"Skipping media-only message (no text)")
            return PlainTextResponse(content="", media_type="text/xml")

        # Initialize WhatsApp client
        mock_mode = not settings.twilio_account_sid
        if mock_mode:
            logger.info("🔧 WhatsApp client in MOCK mode (no TWILIO credentials)")
        else:
            logger.info("✅ WhatsApp client in REAL mode")

        whatsapp_client = WhatsAppClient(mock_mode=mock_mode)

        # Initialize message router
        message_router = MessageRouter(db=db, whatsapp_client=whatsapp_client)

        # Route the message
        # Note: phone_number_id is not used by Twilio, pass our number for org lookup
        await message_router.route_message(
            phone_number_id=our_number,
            sender_phone=sender_phone,
            message_id=MessageSid,
            message_content=Body,
            sender_name=ProfileName,
        )

        # Return empty TwiML (we send responses via the API, not TwiML)
        return PlainTextResponse(content="", media_type="text/xml")

    except Exception as e:
        logger.error(f"❌ Error processing Twilio webhook: {e}", exc_info=True)
        # Return empty response to avoid Twilio retries
        return PlainTextResponse(content="", media_type="text/xml")


@router.get("/whatsapp/status", status_code=status.HTTP_200_OK)
async def webhook_status() -> dict[str, str]:
    """Health check endpoint for webhook configuration."""
    return {
        "status": "ok",
        "provider": "twilio",
        "whatsapp_number": settings.twilio_whatsapp_number or "not configured",
    }


# =============================================================================
# Meta Cloud API Webhook Endpoints
# =============================================================================


def _verify_meta_signature(payload: bytes, signature: str, app_secret: str) -> bool:
    """Verify Meta webhook signature using HMAC-SHA256.

    Args:
        payload: Raw request body bytes
        signature: X-Hub-Signature-256 header value (format: "sha256=...")
        app_secret: Meta App Secret

    Returns:
        True if signature is valid
    """
    if not signature or not signature.startswith("sha256="):
        return False

    expected_signature = hmac.new(
        app_secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    provided_signature = signature[7:]  # Remove "sha256=" prefix

    return hmac.compare_digest(expected_signature, provided_signature)


def _extract_message_from_meta_payload(
    payload: dict[str, Any],
) -> dict[str, Any] | None:
    """Extract message data from Meta Cloud API webhook payload.

    Meta's webhook payload is deeply nested:
    {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "<WABA_ID>",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "...",
                        "phone_number_id": "..."
                    },
                    "contacts": [{"profile": {"name": "..."}, "wa_id": "..."}],
                    "messages": [{
                        "from": "...",
                        "id": "...",
                        "timestamp": "...",
                        "text": {"body": "..."},
                        "type": "text"
                    }]
                },
                "field": "messages"
            }]
        }]
    }

    Args:
        payload: Parsed webhook JSON

    Returns:
        Dict with phone_number_id, sender_phone, message_id, message_content, sender_name
        or None if not a message webhook
    """
    if payload.get("object") != "whatsapp_business_account":
        return None

    entries = payload.get("entry", [])
    if not entries:
        return None

    for entry in entries:
        changes = entry.get("changes", [])
        for change in changes:
            if change.get("field") != "messages":
                continue

            value = change.get("value", {})
            metadata = value.get("metadata", {})
            phone_number_id = metadata.get("phone_number_id")

            messages = value.get("messages", [])
            if not messages:
                # This might be a status update, not a message
                continue

            message = messages[0]
            message_type = message.get("type")

            # Extract message content based on type
            if message_type == "text":
                message_content = message.get("text", {}).get("body", "")
            elif message_type == "button":
                # Button reply
                message_content = message.get("button", {}).get("text", "")
            elif message_type == "interactive":
                # Interactive list/button reply
                interactive = message.get("interactive", {})
                if interactive.get("type") == "button_reply":
                    message_content = interactive.get("button_reply", {}).get("title", "")
                elif interactive.get("type") == "list_reply":
                    message_content = interactive.get("list_reply", {}).get("title", "")
                else:
                    message_content = ""
            else:
                # Unsupported type (image, audio, document, etc.)
                logger.info(f"Skipping unsupported message type: {message_type}")
                return None

            # Extract sender info
            contacts = value.get("contacts", [])
            sender_name = None
            if contacts:
                sender_name = contacts[0].get("profile", {}).get("name")

            sender_phone = message.get("from", "")
            # Add + prefix if not present
            if sender_phone and not sender_phone.startswith("+"):
                sender_phone = f"+{sender_phone}"

            return {
                "phone_number_id": phone_number_id,
                "sender_phone": sender_phone,
                "message_id": message.get("id"),
                "message_content": message_content,
                "sender_name": sender_name,
            }

    return None


@router.get("/whatsapp/meta", status_code=status.HTTP_200_OK)
async def verify_meta_webhook(
    hub_mode: str | None = Query(None, alias="hub.mode"),
    hub_verify_token: str | None = Query(None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(None, alias="hub.challenge"),
) -> PlainTextResponse:
    """Meta webhook verification endpoint.

    Meta sends a GET request with challenge parameters when configuring the webhook.
    We must verify the token and echo back the challenge.

    Args:
        hub_mode: Should be "subscribe"
        hub_verify_token: Token to verify (must match our configured token)
        hub_challenge: Challenge string to echo back

    Returns:
        PlainTextResponse with the challenge string
    """
    logger.info(
        f"📝 Meta webhook verification request:\n"
        f"  hub.mode: {hub_mode}\n"
        f"  hub.verify_token: {hub_verify_token}\n"
        f"  hub.challenge: {hub_challenge[:20] if hub_challenge else 'None'}..."
    )

    if hub_mode == "subscribe" and hub_verify_token == settings.meta_webhook_verify_token:
        logger.info("✅ Meta webhook verification successful")
        return PlainTextResponse(content=hub_challenge or "", media_type="text/plain")

    logger.warning(
        f"❌ Meta webhook verification failed: "
        f"mode={hub_mode}, token_match={hub_verify_token == settings.meta_webhook_verify_token}"
    )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Verification failed",
    )


@router.post("/whatsapp/meta", status_code=status.HTTP_200_OK)
async def receive_meta_webhook(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, str]:
    """Receive incoming WhatsApp messages from Meta Cloud API.

    This endpoint receives webhooks from Meta when customers message
    businesses' connected WhatsApp numbers.

    Args:
        request: FastAPI request object
        db: Database session

    Returns:
        Acknowledgment response
    """
    # Get raw body for signature verification
    body = await request.body()

    # Verify signature (skip in development if secret not configured)
    signature = request.headers.get("X-Hub-Signature-256", "")
    if settings.meta_app_secret:
        if not _verify_meta_signature(body, signature, settings.meta_app_secret):
            logger.warning("❌ Meta webhook signature verification failed")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid signature",
            )
    elif settings.is_production:
        logger.error("❌ META_APP_SECRET not configured in production!")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook not configured",
        )
    else:
        logger.warning("⚠️  Skipping signature verification (META_APP_SECRET not set)")

    # Parse JSON payload
    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"❌ Failed to parse Meta webhook payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    logger.info(
        f"\n{'='*80}\n"
        f"📬 META WEBHOOK RECEIVED\n"
        f"{'='*80}\n"
        f"  Object: {payload.get('object')}\n"
        f"  Entries: {len(payload.get('entry', []))}\n"
        f"{'='*80}"
    )

    # Extract message from nested payload
    message_data = _extract_message_from_meta_payload(payload)

    if not message_data:
        # Not a message webhook (could be status update, etc.)
        logger.info("ℹ️  Meta webhook is not a message - acknowledging without processing")
        return {"status": "ok", "message": "acknowledged"}

    logger.info(
        f"  📨 Message extracted:\n"
        f"    Phone Number ID: {message_data['phone_number_id']}\n"
        f"    From: {message_data['sender_phone']} ({message_data['sender_name'] or 'Unknown'})\n"
        f"    Message ID: {message_data['message_id']}\n"
        f"    Content: {message_data['message_content'][:100]}..."
    )

    try:
        # Initialize WhatsApp client (not mock - we have real Meta credentials)
        whatsapp_client = WhatsAppClient(mock_mode=False)

        # Initialize message router
        message_router = MessageRouter(db=db, whatsapp_client=whatsapp_client)

        # Route the message
        result = await message_router.route_message(
            phone_number_id=message_data["phone_number_id"],
            sender_phone=message_data["sender_phone"],
            message_id=message_data["message_id"],
            message_content=message_data["message_content"],
            sender_name=message_data["sender_name"],
        )

        logger.info(f"✅ Meta webhook processed: {result.get('status')}")
        return {"status": "ok", "route": result.get("route", "unknown")}

    except Exception as e:
        logger.error(f"❌ Error processing Meta webhook: {e}", exc_info=True)
        # Return 200 to prevent Meta from retrying
        # Log the error for debugging
        return {"status": "error", "message": str(e)}

"""Organization service - business logic for organizations."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Organization, OrganizationStatus
from app.schemas.organization import (
    OrganizationConnectWhatsApp,
    OrganizationCreate,
    OrganizationUpdate,
)


async def get_organization(db: AsyncSession, org_id: UUID) -> Organization | None:
    """Get organization by ID."""
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    return result.scalar_one_or_none()


async def get_organization_by_whatsapp_phone_id(
    db: AsyncSession, phone_number_id: str
) -> Organization | None:
    """Get organization by WhatsApp phone number ID."""
    result = await db.execute(
        select(Organization).where(
            Organization.whatsapp_phone_number_id == phone_number_id
        )
    )
    return result.scalar_one_or_none()


async def create_organization(
    db: AsyncSession, org_data: OrganizationCreate
) -> Organization:
    """Create a new organization."""
    org = Organization(
        name=org_data.name,
        phone_country_code=org_data.phone_country_code,
        phone_number=org_data.phone_number,
        timezone=org_data.timezone,
        settings=org_data.settings,
        status=OrganizationStatus.ONBOARDING.value,
    )
    db.add(org)
    await db.flush()
    await db.refresh(org)
    return org


async def update_organization(
    db: AsyncSession, org: Organization, org_data: OrganizationUpdate
) -> Organization:
    """Update an organization."""
    update_dict = org_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(org, key, value)
    await db.flush()
    await db.refresh(org)
    return org


async def connect_whatsapp(
    db: AsyncSession, org: Organization, whatsapp_data: OrganizationConnectWhatsApp
) -> Organization:
    """Connect WhatsApp to organization via Embedded Signup."""
    org.whatsapp_phone_number_id = whatsapp_data.whatsapp_phone_number_id
    org.whatsapp_waba_id = whatsapp_data.whatsapp_waba_id
    org.status = OrganizationStatus.ACTIVE.value
    await db.flush()
    await db.refresh(org)
    return org

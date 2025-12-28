"""Staff service - business logic for staff management."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Staff
from app.schemas.staff import StaffCreate, StaffUpdate


async def get_staff(db: AsyncSession, staff_id: UUID) -> Staff | None:
    """Get staff member by ID."""
    result = await db.execute(select(Staff).where(Staff.id == staff_id))
    return result.scalar_one_or_none()


async def get_staff_by_phone(
    db: AsyncSession, organization_id: UUID, phone_number: str
) -> Staff | None:
    """Get staff member by phone number within an organization.

    This is THE key function for staff identification in message routing.
    When a message arrives, we check if the sender is a registered staff member.
    """
    result = await db.execute(
        select(Staff).where(
            Staff.organization_id == organization_id,
            Staff.phone_number == phone_number,
            Staff.is_active == True,
        )
    )
    return result.scalar_one_or_none()


async def list_staff(
    db: AsyncSession, organization_id: UUID, location_id: UUID | None = None
) -> list[Staff]:
    """List all staff members for an organization, optionally filtered by location."""
    query = select(Staff).where(Staff.organization_id == organization_id)
    if location_id:
        query = query.where(Staff.location_id == location_id)
    result = await db.execute(query.order_by(Staff.name))
    return list(result.scalars().all())


async def create_staff(
    db: AsyncSession, organization_id: UUID, staff_data: StaffCreate
) -> Staff:
    """Create a new staff member."""
    staff = Staff(
        organization_id=organization_id,
        location_id=staff_data.location_id,
        name=staff_data.name,
        phone_number=staff_data.phone_number,
        role=staff_data.role,
        permissions=staff_data.permissions,
        is_active=staff_data.is_active,
        settings=staff_data.settings,
    )
    db.add(staff)
    await db.flush()
    await db.refresh(staff)
    return staff


async def update_staff(
    db: AsyncSession, staff: Staff, staff_data: StaffUpdate
) -> Staff:
    """Update a staff member."""
    update_dict = staff_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(staff, key, value)
    await db.flush()
    await db.refresh(staff)
    return staff


async def delete_staff(db: AsyncSession, staff: Staff) -> None:
    """Delete a staff member (soft delete by setting is_active=False)."""
    staff.is_active = False
    await db.flush()

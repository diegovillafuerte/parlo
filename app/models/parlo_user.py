"""ParloUser model - represents employees and owners who use Parlo."""

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.appointment import Appointment
    from app.models.availability import Availability
    from app.models.location import Location
    from app.models.organization import Organization
    from app.models.service_type import ServiceType
    from app.models.spot import Spot


class ParloUserRole(str, Enum):
    """Parlo user role enum."""

    OWNER = "owner"
    EMPLOYEE = "employee"


class ParloUserPermissionLevel(str, Enum):
    """Permission levels for staff members.

    Determines what actions a staff member can perform.
    See docs/PROJECT_SPEC.md for full permission matrix.
    """

    OWNER = "owner"  # Full access to everything
    ADMIN = "admin"  # Can manage staff, see all data
    STAFF = "staff"  # Can view schedule, create bookings
    VIEWER = "viewer"  # Read-only access


class ParloUser(Base, UUIDMixin, TimestampMixin):
    """People who provide services - also users who can interact via WhatsApp."""

    __tablename__ = "parlo_users"
    __table_args__ = (
        UniqueConstraint("organization_id", "phone_number", name="uq_parlo_user_org_phone"),
        Index("ix_parlo_user_phone_number", "phone_number"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True
    )
    default_spot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("spots.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # Their personal WhatsApp - used to identify them as parlo_user
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ParloUserRole.EMPLOYEE.value
    )
    permissions: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
    )  # {can_view_schedule: true, can_book: true, can_cancel: true, ...}
    permission_level: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ParloUserPermissionLevel.STAFF.value
    )  # owner, admin, staff, viewer - see docs/PROJECT_SPEC.md
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    settings: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # First message timestamp - NULL means never messaged via WhatsApp yet
    # Set on the first WhatsApp message from this staff member
    # Used to detect staff who need onboarding vs already-onboarded staff
    first_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="parlo_users"
    )
    location: Mapped["Location | None"] = relationship("Location", back_populates="parlo_users")
    default_spot: Mapped["Spot | None"] = relationship("Spot", back_populates="parlo_users")
    appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment", back_populates="parlo_user", foreign_keys="Appointment.parlo_user_id"
    )
    availability: Mapped[list["Availability"]] = relationship(
        "Availability", back_populates="parlo_user", cascade="all, delete-orphan"
    )
    # Services this parlo_user can perform
    service_types: Mapped[list["ServiceType"]] = relationship(
        "ServiceType",
        secondary="parlo_user_service_types",
        back_populates="parlo_users",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<ParloUser(id={self.id}, name='{self.name}', role='{self.role}', phone='{self.phone_number}')>"

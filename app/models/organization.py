"""Organization model - represents a business using Yume."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.appointment import Appointment
    from app.models.conversation import Conversation
    from app.models.end_customer import EndCustomer
    from app.models.execution_trace import ExecutionTrace
    from app.models.location import Location
    from app.models.service_type import ServiceType
    from app.models.yume_user import YumeUser


class OrganizationStatus(str, Enum):
    """Organization status enum."""

    ONBOARDING = "onboarding"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CHURNED = "churned"


class Organization(Base, UUIDMixin, TimestampMixin):
    """The business entity (e.g., 'Barbería Don Carlos')."""

    __tablename__ = "organizations"

    # Basic business info (name nullable during onboarding)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone_country_code: Mapped[str] = mapped_column(String(10), nullable=False)  # +52
    phone_number: Mapped[str] = mapped_column(String(50), nullable=False)
    whatsapp_phone_number_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True, unique=True, index=True
    )
    whatsapp_waba_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True
    )
    timezone: Mapped[str] = mapped_column(
        String(50), nullable=False, default="America/Mexico_City"
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=OrganizationStatus.ONBOARDING.value,
    )
    settings: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Onboarding progress tracking (replaces OnboardingSession model)
    onboarding_state: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="initiated",
    )

    # Collected data during onboarding (progressive)
    # Structure: { "business_name": "...", "owner_name": "...", "services": [...], ... }
    onboarding_data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    # AI conversation history during onboarding
    onboarding_conversation_context: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    # For abandoned session detection
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    locations: Mapped[list["Location"]] = relationship(
        "Location", back_populates="organization", cascade="all, delete-orphan"
    )
    yume_users: Mapped[list["YumeUser"]] = relationship(
        "YumeUser", back_populates="organization", cascade="all, delete-orphan"
    )
    service_types: Mapped[list["ServiceType"]] = relationship(
        "ServiceType", back_populates="organization", cascade="all, delete-orphan"
    )
    end_customers: Mapped[list["EndCustomer"]] = relationship(
        "EndCustomer", back_populates="organization", cascade="all, delete-orphan"
    )
    appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment", back_populates="organization", cascade="all, delete-orphan"
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation", back_populates="organization", cascade="all, delete-orphan"
    )
    execution_traces: Mapped[list["ExecutionTrace"]] = relationship(
        "ExecutionTrace", back_populates="organization", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Organization(id={self.id}, name='{self.name}', status='{self.status}')>"

"""Pydantic schemas for Availability."""

from datetime import date, datetime, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# Base schema for recurring availability
class RecurringAvailabilityBase(BaseModel):
    """Base schema for recurring availability."""

    day_of_week: int = Field(..., ge=0, le=6, description="Day of week (0=Monday, 6=Sunday)")
    start_time: time = Field(..., description="Start time")
    end_time: time = Field(..., description="End time")


# Base schema for exception availability
class ExceptionAvailabilityBase(BaseModel):
    """Base schema for exception availability."""

    exception_date: date = Field(..., description="Specific date for exception")
    is_available: bool = Field(..., description="Is available on this date")
    start_time: time | None = Field(None, description="Start time (if available)")
    end_time: time | None = Field(None, description="End time (if available)")


# Schema for creating recurring availability
class RecurringAvailabilityCreate(RecurringAvailabilityBase):
    """Schema for creating recurring availability."""

    staff_id: UUID = Field(..., description="Staff member ID")


# Schema for creating exception availability
class ExceptionAvailabilityCreate(ExceptionAvailabilityBase):
    """Schema for creating exception availability."""

    staff_id: UUID = Field(..., description="Staff member ID")


# Generic response schema
class AvailabilityResponse(BaseModel):
    """Schema for availability responses."""

    id: UUID
    parlo_user_id: UUID = Field(
        ...,
        validation_alias="staff_id",
        serialization_alias="staff_id",
        description="Staff member ID",
    )
    type: str  # recurring or exception

    # For recurring
    day_of_week: int | None
    start_time: time | None
    end_time: time | None

    # For exceptions
    exception_date: date | None
    is_available: bool | None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# Schema for requesting available slots
class AvailableSlotRequest(BaseModel):
    """Schema for requesting available appointment slots."""

    service_type_id: UUID = Field(..., description="Service type ID")
    date_from: date = Field(..., description="Start date for search")
    date_to: date | None = Field(None, description="End date for search (defaults to date_from)")
    staff_id: UUID | None = Field(None, description="Specific staff member (optional)")


# Schema for available slot response
class AvailableSlot(BaseModel):
    """Schema for an available appointment slot."""

    start_time: datetime = Field(..., description="Slot start time (UTC)")
    end_time: datetime = Field(..., description="Slot end time (UTC)")
    staff_id: UUID = Field(..., description="Staff member for this slot")
    staff_name: str = Field(..., description="Staff member name")

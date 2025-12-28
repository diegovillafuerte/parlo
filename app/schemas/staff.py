"""Pydantic schemas for Staff."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# Base schema
class StaffBase(BaseModel):
    """Base staff schema with common fields."""

    name: str = Field(..., min_length=1, max_length=255, description="Staff member name")
    phone_number: str = Field(
        ..., description="Personal WhatsApp number - used to identify them as staff"
    )
    role: str = Field(
        default="employee", description="Role: owner or employee"
    )
    permissions: dict[str, Any] = Field(
        default_factory=dict,
        description="Permissions: {can_view_schedule: true, can_book: true, ...}",
    )
    is_active: bool = Field(default=True, description="Is the staff member active")


# Schema for creating a staff member
class StaffCreate(StaffBase):
    """Schema for creating a new staff member."""

    location_id: UUID | None = Field(None, description="Location ID (null = all locations)")
    settings: dict[str, Any] = Field(default_factory=dict, description="Staff settings")


# Schema for updating a staff member
class StaffUpdate(BaseModel):
    """Schema for updating a staff member (all fields optional)."""

    name: str | None = Field(None, min_length=1, max_length=255)
    phone_number: str | None = None
    role: str | None = None
    location_id: UUID | None = None
    permissions: dict[str, Any] | None = None
    is_active: bool | None = None
    settings: dict[str, Any] | None = None

    model_config = ConfigDict(extra="forbid")


# Response schema
class StaffResponse(StaffBase):
    """Schema for staff responses."""

    id: UUID
    organization_id: UUID
    location_id: UUID | None
    settings: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

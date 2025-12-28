"""Pydantic schemas for Location."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# Base schema
class LocationBase(BaseModel):
    """Base location schema with common fields."""

    name: str = Field(..., min_length=1, max_length=255, description="Location name")
    address: str | None = Field(None, description="Physical address")
    is_primary: bool = Field(default=True, description="Is this the primary location")
    business_hours: dict[str, Any] = Field(
        default_factory=dict,
        description="Business hours by day: {mon: {open: '10:00', close: '20:00'}, ...}",
    )


# Schema for creating a location
class LocationCreate(LocationBase):
    """Schema for creating a new location."""

    pass


# Schema for updating a location
class LocationUpdate(BaseModel):
    """Schema for updating a location (all fields optional)."""

    name: str | None = Field(None, min_length=1, max_length=255)
    address: str | None = None
    is_primary: bool | None = None
    business_hours: dict[str, Any] | None = None

    model_config = ConfigDict(extra="forbid")


# Response schema
class LocationResponse(LocationBase):
    """Schema for location responses."""

    id: UUID
    organization_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

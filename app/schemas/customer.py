"""Pydantic schemas for Customer."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# Base schema
class CustomerBase(BaseModel):
    """Base customer schema with common fields."""

    phone_number: str = Field(..., description="Customer phone number - primary identifier")
    name: str | None = Field(None, description="Customer name (learned over time)")
    email: EmailStr | None = Field(None, description="Customer email (optional)")
    notes: str | None = Field(None, description="Business owner's notes about customer")


# Schema for creating a customer (incremental identity - only phone required)
class CustomerCreate(BaseModel):
    """Schema for creating a new customer - only phone required initially."""

    phone_number: str = Field(..., description="Customer phone number")
    name: str | None = None
    email: EmailStr | None = None
    notes: str | None = None
    settings: dict[str, Any] = Field(default_factory=dict, description="Customer settings")


# Schema for updating a customer
class CustomerUpdate(BaseModel):
    """Schema for updating a customer (all fields optional)."""

    phone_number: str | None = None
    name: str | None = None
    email: EmailStr | None = None
    notes: str | None = None
    settings: dict[str, Any] | None = None

    model_config = ConfigDict(extra="forbid")


# Response schema
class CustomerResponse(CustomerBase):
    """Schema for customer responses."""

    id: UUID
    organization_id: UUID
    settings: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

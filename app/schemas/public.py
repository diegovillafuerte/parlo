"""Schemas for public (unauthenticated) endpoints."""

from pydantic import BaseModel


class BusinessSiteService(BaseModel):
    name: str
    description: str | None = None
    duration_minutes: int
    price_cents: int
    currency: str


class BusinessSiteLocation(BaseModel):
    address: str | None = None
    business_hours: dict


class BusinessSiteResponse(BaseModel):
    business_name: str
    slug: str
    location: BusinessSiteLocation
    services: list[BusinessSiteService]
    whatsapp_number: str | None = None
    timezone: str

"""Main API router for v1 endpoints."""

from fastapi import APIRouter

from app.api.v1 import (
    appointments,
    availability,
    customers,
    organizations,
    services,
    staff,
    webhooks,
)

router = APIRouter()

# Include all sub-routers
router.include_router(organizations.router)
router.include_router(services.router)
router.include_router(staff.router)
router.include_router(customers.router)
router.include_router(appointments.router)
router.include_router(availability.router)
router.include_router(webhooks.router)


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "message": "Yume API is running"}

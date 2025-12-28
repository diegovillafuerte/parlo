"""Dependency injection for API endpoints."""

from collections.abc import AsyncGenerator
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Organization
from app.services import organization as org_service

__all__ = ["get_db", "AsyncSession", "get_organization_dependency", "PaginationParams"]


# Database session dependency
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session - alias for get_db."""
    async for session in get_db():
        yield session


# Organization lookup dependency
async def get_organization_dependency(
    org_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Organization:
    """Get organization by ID or raise 404."""
    org = await org_service.get_organization(db, org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization {org_id} not found",
        )
    return org


# Pagination parameters
class PaginationParams:
    """Pagination query parameters."""

    def __init__(
        self,
        skip: Annotated[int, Query(ge=0, description="Number of records to skip")] = 0,
        limit: Annotated[
            int, Query(ge=1, le=100, description="Maximum number of records to return")
        ] = 50,
    ):
        self.skip = skip
        self.limit = limit

"""Insight-related Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class InsightSummary(BaseModel):
    """Insight summary for task list view."""

    id: UUID
    organization_id: UUID
    organization_name: str | None = None
    conversation_id: UUID
    insight_type: str
    title: str
    description: str
    severity: str
    quality_score: int
    conversation_summary: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class InsightStatusUpdate(BaseModel):
    """Request to update insight status."""

    status: str = Field(..., description="New status: 'open', 'acknowledged', or 'resolved'")


class InsightStatsResponse(BaseModel):
    """Insight statistics summary."""

    total: int
    open: int
    acknowledged: int
    resolved: int
    by_type: dict
    avg_quality_score: float | None

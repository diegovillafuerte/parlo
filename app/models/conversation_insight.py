"""Conversation insight model - AI-generated analysis of conversations."""

import uuid
from enum import Enum

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class InsightType(str, Enum):
    BUG = "bug"
    FEATURE_REQUEST = "feature_request"
    FOLLOW_UP = "follow_up"


class InsightSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class InsightStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class ConversationInsight(Base, UUIDMixin, TimestampMixin):
    """An actionable insight from AI analysis of a conversation."""

    __tablename__ = "conversation_insights"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    insight_type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False, default=InsightSeverity.MEDIUM.value
    )
    quality_score: Mapped[int] = mapped_column(Integer, nullable=False)
    conversation_summary: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=InsightStatus.OPEN.value
    )

    # Relationships
    organization = relationship("Organization")
    conversation = relationship("Conversation")

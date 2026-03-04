"""Conversation analysis service - AI-powered conversation insights."""

import json
import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.client import OpenAIClient
from app.models.conversation import Conversation
from app.models.conversation_insight import (
    ConversationInsight,
    InsightSeverity,
    InsightStatus,
    InsightType,
)
from app.models.message import Message

logger = logging.getLogger(__name__)

ANALYSIS_PROMPT = """\
You are a conversation quality analyst for Parlo, a WhatsApp-based AI scheduling \
assistant for beauty businesses in Mexico. The AI assistant communicates in Mexican Spanish.

Analyze the following conversation transcript and produce a JSON response with this exact structure:

{
  "quality_score": <integer 1-10>,
  "conversation_summary": "<1-2 sentence summary of what happened>",
  "insights": [
    {
      "type": "bug" | "feature_request" | "follow_up",
      "title": "<short title, max 100 chars>",
      "description": "<detailed explanation>",
      "severity": "low" | "medium" | "high" | "critical"
    }
  ]
}

## Scoring Guide (quality_score)
- 10: Perfect interaction, user got what they needed efficiently
- 7-9: Good interaction with minor issues (extra back-and-forth, slightly unclear)
- 4-6: Mediocre - user got partially served or interaction was confusing
- 1-3: Bad - user frustrated, AI made errors, or total failure

## What to flag as "bug"
- AI gave wrong information (wrong price, wrong time, wrong availability)
- AI failed to call a tool when it should have
- AI called a tool with wrong parameters
- AI responded in English when it should be in Spanish
- Booking was made with incorrect details
- AI hallucinated services, staff, or times that don't exist
- AI got stuck in a loop or repeated itself
- Staff tool returned incorrect data (wrong schedule, wrong permissions)
- Onboarding flow got stuck or gave wrong instructions

## What to flag as "feature_request" (implicit - the user did NOT explicitly ask for a feature)
- User sent media (image/audio/PDF/document) that the system can't process
- User asked about something the system doesn't support (payments, waitlist, group bookings, etc.)
- User wanted to do something reasonable that has no tool (directions, loyalty points, etc.)
- User tried to communicate in a way the system doesn't handle well
- Staff asked for functionality that doesn't exist yet
- During onboarding, the business needed something the system can't configure

## What to flag as "follow_up"
- User expressed dissatisfaction or frustration
- User's issue was not fully resolved
- Booking was made but something seemed off (wrong service, uncertain time)
- User was handed off to human but no resolution is visible
- User abandoned the conversation mid-flow
- Onboarding was not completed
- Staff had a question that the AI couldn't answer

## Severity Guide
- critical: Data corruption, wrong booking made, user actively angry
- high: Feature broken, user confused and left without resolution
- medium: Suboptimal experience but user eventually got served
- low: Minor UX issue, cosmetic, or very rare edge case

## Rules
- Return an empty insights array if the conversation was clean (no issues)
- Always include quality_score and conversation_summary even if no insights
- Be concise in titles, detailed in descriptions
- Focus on actionable insights, not theoretical concerns
- Write all analysis in English (even though conversations are in Spanish)
- If the conversation is too short (just a greeting) give quality_score 5 and no insights

Respond ONLY with valid JSON. No markdown, no explanation outside the JSON."""

VALID_TYPES = {t.value for t in InsightType}
VALID_SEVERITIES = {s.value for s in InsightSeverity}


def _build_transcript(messages: list[Message]) -> str:
    """Build a human-readable transcript from messages."""
    sender_labels = {
        "end_customer": "CUSTOMER",
        "ai": "AI",
        "parlo_user": "STAFF",
    }
    lines = []
    for msg in messages:
        label = sender_labels.get(msg.sender_type, "UNKNOWN")
        content_prefix = ""
        if msg.content_type and msg.content_type != "text":
            content_prefix = f"[{msg.content_type.upper()}] "
        lines.append(f"[{label}] {content_prefix}{msg.content}")
    return "\n".join(lines)


async def analyze_and_store_insights(
    db: AsyncSession,
    conversation_id: UUID,
) -> dict:
    """Analyze a conversation and store insights.

    Returns dict with results summary.
    """
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        logger.warning(f"Conversation {conversation_id} not found for analysis")
        return {"error": "not_found"}

    messages = sorted(conversation.messages, key=lambda m: m.created_at)

    if len(messages) < 2:
        conversation.analyzed_at = datetime.now(UTC)
        return {"skipped": True, "reason": "too_few_messages"}

    # Build transcript, truncating if too long
    transcript = _build_transcript(messages)
    if len(transcript) > 50000:
        transcript = transcript[-50000:]

    # Load org name for context
    from app.models.organization import Organization

    org_result = await db.execute(
        select(Organization.name).where(Organization.id == conversation.organization_id)
    )
    org_name = org_result.scalar_one_or_none() or "Unknown"

    # Call OpenAI
    client = OpenAIClient()
    if not client.is_configured:
        return {"error": "openai_not_configured"}

    try:
        response = client.create_message(
            system_prompt=ANALYSIS_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Business: {org_name}\n\nTranscript:\n{transcript}",
                }
            ],
            tools=None,
            max_tokens=1024,
            model="gpt-4.1-mini",
        )
        response_text = client.extract_text_response(response)
        analysis = json.loads(response_text)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON from analysis of conversation {conversation_id}")
        return {"error": "invalid_json"}
    except Exception as e:
        logger.error(f"Failed to analyze conversation {conversation_id}: {e}")
        return {"error": str(e)}

    # Delete existing insights for re-analysis
    await db.execute(
        delete(ConversationInsight).where(ConversationInsight.conversation_id == conversation_id)
    )

    # Parse and store insights
    quality_score = max(1, min(10, analysis.get("quality_score", 5)))
    summary = analysis.get("conversation_summary", "")[:500]
    insights_data = analysis.get("insights", [])
    created_count = 0

    for item in insights_data:
        insight_type = item.get("type", "")
        if insight_type not in VALID_TYPES:
            continue

        severity = item.get("severity", InsightSeverity.MEDIUM.value)
        if severity not in VALID_SEVERITIES:
            severity = InsightSeverity.MEDIUM.value

        insight = ConversationInsight(
            organization_id=conversation.organization_id,
            conversation_id=conversation.id,
            insight_type=insight_type,
            title=item.get("title", "Untitled")[:200],
            description=item.get("description", ""),
            severity=severity,
            quality_score=quality_score,
            conversation_summary=summary,
            status=InsightStatus.OPEN.value,
        )
        db.add(insight)
        created_count += 1

    conversation.analyzed_at = datetime.now(UTC)

    return {
        "conversation_id": str(conversation_id),
        "quality_score": quality_score,
        "insights_created": created_count,
    }

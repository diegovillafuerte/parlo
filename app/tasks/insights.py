"""Conversation analysis tasks."""

import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.insights.analyze_conversation")
def analyze_conversation(conversation_id: str) -> dict:
    """Analyze a single conversation and create insight records.

    Fired when a CustomerFlowSession reaches a terminal state,
    or by the periodic sweep task.

    Args:
        conversation_id: UUID of the conversation to analyze

    Returns:
        Dict with analysis results
    """
    import asyncio

    async def _analyze():
        from uuid import UUID

        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

        from app.config import get_settings
        from app.services.conversation_analysis import analyze_and_store_insights

        settings = get_settings()
        engine = create_async_engine(settings.async_database_url)
        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        try:
            async with session_factory() as db:
                result = await analyze_and_store_insights(db, UUID(conversation_id))
                await db.commit()
                return result
        finally:
            await engine.dispose()

    return asyncio.run(_analyze())


@celery_app.task(name="app.tasks.insights.sweep_unanalyzed_conversations")
def sweep_unanalyzed_conversations() -> dict:
    """Periodic task: find idle, un-analyzed conversations and queue analysis.

    Finds all conversations (customer + staff) where:
    - analyzed_at IS NULL or analyzed_at < last_message_at
    - last_message_at is > 30 minutes ago (idle)
    - message count >= 2

    Returns:
        Dict with count of queued analyses
    """
    import asyncio

    async def _sweep():
        from datetime import UTC, datetime, timedelta

        from sqlalchemy import func, select
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

        from app.config import get_settings
        from app.models import Conversation, Message

        settings = get_settings()
        engine = create_async_engine(settings.async_database_url)
        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        idle_threshold = datetime.now(UTC) - timedelta(minutes=30)
        queued = 0

        try:
            async with session_factory() as db:
                # Subquery: conversations with >= 2 messages
                msg_count_sq = (
                    select(
                        Message.conversation_id,
                        func.count().label("cnt"),
                    )
                    .group_by(Message.conversation_id)
                    .having(func.count() >= 2)
                    .subquery()
                )

                query = (
                    select(Conversation.id)
                    .join(msg_count_sq, Conversation.id == msg_count_sq.c.conversation_id)
                    .where(
                        Conversation.last_message_at < idle_threshold,
                        (Conversation.analyzed_at.is_(None))
                        | (Conversation.analyzed_at < Conversation.last_message_at),
                    )
                    .limit(50)
                )

                result = await db.execute(query)
                conv_ids = [row[0] for row in result.all()]

                for conv_id in conv_ids:
                    analyze_conversation.delay(str(conv_id))
                    queued += 1

                if queued > 0:
                    logger.info(f"Queued {queued} conversations for analysis")

                return {"queued": queued}
        finally:
            await engine.dispose()

    return asyncio.run(_sweep())

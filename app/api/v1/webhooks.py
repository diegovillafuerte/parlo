"""WhatsApp webhook endpoints - receive messages from Meta."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.config import get_settings
from app.schemas.whatsapp import WhatsAppWebhook
from app.services.message_router import MessageRouter
from app.services.whatsapp import WhatsAppClient

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)
settings = get_settings()


@router.get("/whatsapp")
async def verify_webhook(
    mode: Annotated[str | None, Query(alias="hub.mode")] = None,
    token: Annotated[str | None, Query(alias="hub.verify_token")] = None,
    challenge: Annotated[str | None, Query(alias="hub.challenge")] = None,
) -> str | dict:
    """Verify webhook with Meta (GET request).

    Meta calls this endpoint to verify our webhook URL.
    We must return the challenge string if the verify token matches.

    See: https://developers.facebook.com/docs/graph-api/webhooks/getting-started
    """
    logger.info(
        f"Webhook verification request:\n"
        f"  Mode: {mode}\n"
        f"  Token: {token}\n"
        f"  Challenge: {challenge}"
    )

    if mode == "subscribe" and token == settings.meta_webhook_verify_token:
        logger.info("✅ Webhook verification successful")
        return challenge or ""

    logger.warning("❌ Webhook verification failed - invalid token")
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Webhook verification failed",
    )


@router.post("/whatsapp", status_code=status.HTTP_200_OK)
async def receive_webhook(
    request: Request,
    webhook: WhatsAppWebhook,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, str]:
    """Receive incoming WhatsApp messages (POST request).

    This is where ALL WhatsApp messages arrive.
    This endpoint must:
    1. Parse the webhook payload
    2. Extract message details
    3. Route to MessageRouter
    4. Return 200 quickly (Meta expects response within 20 seconds)

    See: https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/components
    """
    logger.info(f"📬 Webhook received: {webhook.object}")

    # Meta expects 200 quickly - we process in background if needed
    # For now, we'll process synchronously since routing is fast

    try:
        # Initialize WhatsApp client (in mock mode for now)
        whatsapp_client = WhatsAppClient(mock_mode=True)

        # Initialize message router
        router = MessageRouter(db=db, whatsapp_client=whatsapp_client)

        # Process each entry in the webhook
        for entry in webhook.entry:
            logger.info(f"Processing entry: {entry.id}")

            for change in entry.changes:
                if change.field != "messages":
                    logger.info(f"Skipping non-message change: {change.field}")
                    continue

                value = change.value

                # Skip if no messages
                if not value.messages:
                    logger.info("No messages in webhook payload")
                    continue

                # Process each message
                for message in value.messages:
                    # Only handle text messages for now
                    if message.type != "text" or not message.text:
                        logger.info(f"Skipping non-text message: {message.type}")
                        continue

                    # Extract sender name from contacts if available
                    sender_name = None
                    if value.contacts:
                        for contact in value.contacts:
                            if contact.wa_id == message.from_:
                                sender_name = contact.profile.name
                                break

                    # Route the message!
                    await router.route_message(
                        phone_number_id=value.metadata.phone_number_id,
                        sender_phone=message.from_,
                        message_id=message.id,
                        message_content=message.text.body,
                        sender_name=sender_name,
                    )

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"❌ Error processing webhook: {e}", exc_info=True)
        # Still return 200 to Meta to avoid retries
        # Log the error for investigation
        return {"status": "error", "message": str(e)}

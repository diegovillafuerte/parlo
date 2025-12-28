"""Message Router - THE CORE of Yume's value proposition.

This module routes incoming WhatsApp messages to the correct handler based on
whether the sender is a registered staff member or a customer.

Critical Flow:
1. Message arrives from WhatsApp
2. Look up organization by phone_number_id
3. 🔍 CRITICAL: Look up sender - are they staff?
4. Route to StaffHandler OR CustomerHandler
5. Process message and send response

This is what enables ONE WhatsApp number to serve TWO different experiences.
"""

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Conversation,
    ConversationStatus,
    Customer,
    Message,
    MessageContentType,
    MessageDirection,
    MessageSenderType,
    Organization,
    Staff,
)
from app.services import customer as customer_service
from app.services import organization as org_service
from app.services import staff as staff_service
from app.services.whatsapp import WhatsAppClient

logger = logging.getLogger(__name__)


class MessageRouter:
    """Routes incoming WhatsApp messages to appropriate handlers."""

    def __init__(self, db: AsyncSession, whatsapp_client: WhatsAppClient):
        """Initialize message router.

        Args:
            db: Database session
            whatsapp_client: WhatsApp API client (can be in mock mode)
        """
        self.db = db
        self.whatsapp = whatsapp_client

    async def route_message(
        self,
        phone_number_id: str,
        sender_phone: str,
        message_id: str,
        message_content: str,
        sender_name: str | None = None,
    ) -> dict[str, str]:
        """Route an incoming WhatsApp message.

        This is THE critical function that determines the entire user experience.

        Args:
            phone_number_id: Our WhatsApp number ID (identifies which org)
            sender_phone: Sender's phone number (identifies staff vs customer)
            message_id: WhatsApp message ID (for deduplication)
            message_content: The message text
            sender_name: Sender's name from WhatsApp profile (optional)

        Returns:
            Dict with routing decision and status
        """
        logger.info(
            f"\n{'='*80}\n"
            f"📨 INCOMING MESSAGE\n"
            f"{'='*80}\n"
            f"  Phone Number ID: {phone_number_id}\n"
            f"  Sender: {sender_phone} ({sender_name or 'Unknown'})\n"
            f"  Message ID: {message_id}\n"
            f"  Content: {message_content}\n"
            f"{'='*80}"
        )

        # Step 1: Check message deduplication
        if await self._message_already_processed(message_id):
            logger.warning(f"⚠️  Message {message_id} already processed - skipping")
            return {"status": "duplicate", "message_id": message_id}

        # Step 2: Lookup organization
        org = await org_service.get_organization_by_whatsapp_phone_id(
            self.db, phone_number_id
        )
        if not org:
            logger.error(
                f"❌ ROUTING ERROR: Unknown phone_number_id: {phone_number_id}\n"
                f"   This WhatsApp number is not registered in our system."
            )
            return {
                "status": "error",
                "reason": "unknown_organization",
                "phone_number_id": phone_number_id,
            }

        logger.info(f"✅ Organization found: {org.name} (ID: {org.id})")

        # Step 3: 🔍 CRITICAL ROUTING DECISION - Check if sender is staff
        staff = await staff_service.get_staff_by_phone(self.db, org.id, sender_phone)

        if staff and staff.is_active:
            # 🎯 STAFF MESSAGE - Route to staff handler
            logger.info(
                f"\n🔵 ROUTING DECISION: STAFF\n"
                f"   Staff Member: {staff.name} (Role: {staff.role})\n"
                f"   → Routing to StaffConversationHandler"
            )
            response_text = await self._handle_staff_message(
                org, staff, message_content, sender_phone, message_id
            )
            sender_type = MessageSenderType.STAFF
        else:
            # 🎯 CUSTOMER MESSAGE - Route to customer handler
            if staff and not staff.is_active:
                logger.info(
                    f"\n🟡 Staff {staff.name} exists but is INACTIVE - treating as customer"
                )

            logger.info(
                f"\n🟢 ROUTING DECISION: CUSTOMER\n"
                f"   → Routing to CustomerConversationHandler\n"
                f"   → Will get_or_create customer with phone {sender_phone}"
            )

            # Get or create customer (incremental identity pattern)
            customer = await customer_service.get_or_create_customer(
                self.db, org.id, sender_phone, name=sender_name
            )
            logger.info(f"   Customer: {customer.name or 'Unknown'} (ID: {customer.id})")

            response_text = await self._handle_customer_message(
                org, customer, message_content, sender_phone, message_id
            )
            sender_type = MessageSenderType.CUSTOMER

        # Step 4: Send response via WhatsApp
        await self.whatsapp.send_text_message(
            phone_number_id=phone_number_id,
            to=sender_phone,
            message=response_text,
        )

        logger.info(
            f"\n✅ MESSAGE ROUTING COMPLETE\n"
            f"   Sender Type: {sender_type.value}\n"
            f"   Response Sent: {response_text[:50]}...\n"
            f"{'='*80}\n"
        )

        await self.db.commit()

        return {
            "status": "success",
            "sender_type": sender_type.value,
            "organization_id": str(org.id),
        }

    async def _handle_staff_message(
        self,
        org: Organization,
        staff: Staff,
        message_content: str,
        sender_phone: str,
        message_id: str,
    ) -> str:
        """Handle message from staff member.

        For now, this is a simple echo handler.
        Later, this will be replaced with AI that has staff tools.

        Args:
            org: Organization
            staff: Staff member
            message_content: Message text
            sender_phone: Staff phone
            message_id: Message ID

        Returns:
            Response text to send back
        """
        # TODO: Replace with AI conversation handler
        # For now, acknowledge and show it worked

        logger.info(f"   Processing staff message with simple handler (AI coming soon)")

        # Store the incoming message
        await self._store_message(
            organization_id=org.id,
            sender_phone=sender_phone,
            message_id=message_id,
            direction=MessageDirection.INBOUND,
            sender_type=MessageSenderType.STAFF,
            content=message_content,
        )

        # Simple response showing staff capabilities
        response = (
            f"Hola {staff.name}! 👋\n\n"
            f"Soy Yume, tu asistente. Reconozco que eres parte del equipo.\n\n"
            f"Pronto podrás:\n"
            f"• Ver tu agenda del día\n"
            f"• Bloquear tiempo personal\n"
            f"• Marcar citas completadas\n"
            f"• Registrar walk-ins\n\n"
            f"(Por ahora estoy en modo de prueba)"
        )

        return response

    async def _handle_customer_message(
        self,
        org: Organization,
        customer: Customer,
        message_content: str,
        sender_phone: str,
        message_id: str,
    ) -> str:
        """Handle message from customer.

        For now, this is a simple echo handler.
        Later, this will be replaced with AI that has customer tools.

        Args:
            org: Organization
            customer: Customer
            message_content: Message text
            sender_phone: Customer phone
            message_id: Message ID

        Returns:
            Response text to send back
        """
        # TODO: Replace with AI conversation handler
        # For now, acknowledge and show it worked

        logger.info(f"   Processing customer message with simple handler (AI coming soon)")

        # Get or create conversation
        conversation = await self._get_or_create_conversation(org.id, customer.id)

        # Store the incoming message
        await self._store_message(
            organization_id=org.id,
            sender_phone=sender_phone,
            message_id=message_id,
            direction=MessageDirection.INBOUND,
            sender_type=MessageSenderType.CUSTOMER,
            content=message_content,
            conversation_id=conversation.id,
        )

        # Simple response showing customer capabilities
        customer_name = customer.name or "cliente"
        response = (
            f"¡Hola {customer_name}! 👋\n\n"
            f"Bienvenido a {org.name}. Soy Yume, tu asistente virtual.\n\n"
            f"Pronto podrás:\n"
            f"• Agendar citas\n"
            f"• Reprogramar citas\n"
            f"• Cancelar citas\n"
            f"• Ver tus próximas citas\n\n"
            f"(Por ahora estoy en modo de prueba)"
        )

        return response

    async def _message_already_processed(self, message_id: str) -> bool:
        """Check if message was already processed (deduplication).

        Args:
            message_id: WhatsApp message ID

        Returns:
            True if message already exists in database
        """
        from sqlalchemy import select

        result = await self.db.execute(
            select(Message).where(Message.whatsapp_message_id == message_id)
        )
        return result.scalar_one_or_none() is not None

    async def _get_or_create_conversation(
        self, organization_id: UUID, customer_id: UUID
    ) -> Conversation:
        """Get or create active conversation for customer.

        Args:
            organization_id: Organization ID
            customer_id: Customer ID

        Returns:
            Active conversation
        """
        from sqlalchemy import select

        # Try to find active conversation
        result = await self.db.execute(
            select(Conversation).where(
                Conversation.organization_id == organization_id,
                Conversation.customer_id == customer_id,
                Conversation.status == ConversationStatus.ACTIVE.value,
            )
        )
        conversation = result.scalar_one_or_none()

        if conversation:
            # Update last message time
            conversation.last_message_at = datetime.now(timezone.utc)
            return conversation

        # Create new conversation
        conversation = Conversation(
            organization_id=organization_id,
            customer_id=customer_id,
            status=ConversationStatus.ACTIVE.value,
            context={},
            last_message_at=datetime.now(timezone.utc),
        )
        self.db.add(conversation)
        await self.db.flush()
        await self.db.refresh(conversation)
        return conversation

    async def _store_message(
        self,
        organization_id: UUID,
        sender_phone: str,
        message_id: str,
        direction: MessageDirection,
        sender_type: MessageSenderType,
        content: str,
        conversation_id: UUID | None = None,
    ) -> Message:
        """Store message in database.

        Args:
            organization_id: Organization ID
            sender_phone: Sender's phone
            message_id: WhatsApp message ID
            direction: Inbound or outbound
            sender_type: Customer, staff, or AI
            content: Message content
            conversation_id: Conversation ID (optional)

        Returns:
            Created message
        """
        message = Message(
            conversation_id=conversation_id,
            direction=direction.value,
            sender_type=sender_type.value,
            content_type=MessageContentType.TEXT.value,
            content=content,
            whatsapp_message_id=message_id,
        )
        self.db.add(message)
        await self.db.flush()
        return message

"""Tests for message router onboarding cases.

Tests for routing Cases 1, 3, 4, 5 as they relate to onboarding
and routing to provisioned business numbers.

Updated to use Organization-based onboarding (no OnboardingSession).
"""

from datetime import UTC
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.models import (
    Location,
    Organization,
    OrganizationStatus,
    ParloUser,
    ParloUserPermissionLevel,
    ParloUserRole,
)
from app.services.message_router import MessageRouter
from app.services.onboarding import OnboardingState

# Aliases for readability
Staff = ParloUser
StaffRole = ParloUserRole

pytestmark = pytest.mark.asyncio


class TestMessageRouterCase1:
    """Tests for Case 1: Unknown sender -> Business Onboarding."""

    async def test_routes_unknown_sender_to_onboarding(self, db, mock_whatsapp_client):
        """Unknown phone number on Parlo Central routes to onboarding flow."""
        router = MessageRouter(db=db, whatsapp_client=mock_whatsapp_client)

        with patch.object(
            router, "_handle_business_onboarding", new_callable=AsyncMock
        ) as mock_handler:
            mock_handler.return_value = "¡Hola! Soy Parlo..."

            result = await router.route_message(
                phone_number_id="PARLO_CENTRAL_ID",  # Not a business number
                sender_phone="+525551234567",  # Unknown sender
                message_id="test_msg_001",
                message_content="Hola, quiero registrar mi negocio",
                sender_name="Carlos",
            )

            assert result["case"] == "1"
            assert result["route"] == "business_onboarding"
            mock_handler.assert_called_once()

    async def test_creates_organization_for_new_user(self, db, mock_whatsapp_client):
        """Creates Organization for new user on first message."""
        router = MessageRouter(db=db, whatsapp_client=mock_whatsapp_client)

        # Mock the AI to avoid actual API calls
        with patch(
            "app.services.onboarding.OnboardingHandler.handle_message",
            new_callable=AsyncMock,
        ) as mock_handle:
            mock_handle.return_value = "¡Hola! Bienvenido a Parlo..."

            await router.route_message(
                phone_number_id="PARLO_CENTRAL_ID",
                sender_phone="+525559999888",
                message_id="test_msg_002",
                message_content="Hola",
                sender_name="Ana",
            )

            # Verify organization was created (with ONBOARDING status)
            from sqlalchemy import select

            result = await db.execute(
                select(Organization).where(Organization.phone_number == "+525559999888")
            )
            org = result.scalar_one_or_none()

            assert org is not None
            assert org.status == OrganizationStatus.ONBOARDING.value

            # Verify owner staff was created
            result = await db.execute(
                select(Staff).where(
                    Staff.organization_id == org.id,
                    Staff.phone_number == "+525559999888",
                )
            )
            staff = result.scalar_one_or_none()
            assert staff is not None
            assert staff.name == "Ana"

    async def test_continues_existing_onboarding_org(
        self, db, mock_whatsapp_client, onboarding_session_collecting_services
    ):
        """Routes to existing onboarding org if one exists."""
        org = onboarding_session_collecting_services
        router = MessageRouter(db=db, whatsapp_client=mock_whatsapp_client)

        with patch(
            "app.services.onboarding.OnboardingHandler.handle_message",
            new_callable=AsyncMock,
        ) as mock_handle:
            mock_handle.return_value = "Perfecto, ¿qué servicios ofreces?"

            result = await router.route_message(
                phone_number_id="PARLO_CENTRAL_ID",
                sender_phone=org.phone_number,
                message_id="test_msg_003",
                message_content="Corte de cabello $150",
                sender_name="Maria",
            )

            # Should continue onboarding (case 1b since org exists)
            assert result["case"] in ["1", "1b"]
            mock_handle.assert_called_once()


class TestMessageRouterBusinessNumberRouting:
    """Tests for routing to business's provisioned number."""

    async def test_routes_to_org_by_whatsapp_phone_number_id(
        self, db, mock_whatsapp_client, organization_with_twilio_number
    ):
        """Message to provisioned number finds correct org."""
        router = MessageRouter(db=db, whatsapp_client=mock_whatsapp_client)

        # Use the actual provisioned phone number as phone_number_id
        phone_number_id = organization_with_twilio_number.whatsapp_phone_number_id

        # Mock the customer flow handler
        with patch(
            "app.services.customer_flows.CustomerFlowHandler.handle_message",
            new_callable=AsyncMock,
        ) as mock_handler:
            mock_handler.return_value = "¡Hola! ¿Te gustaría agendar una cita?"

            result = await router.route_message(
                phone_number_id=phone_number_id,
                sender_phone="+525577778888",  # Some customer
                message_id="test_msg_004",
                message_content="Hola, quiero una cita",
                sender_name="Customer",
            )

            assert result["status"] == "success"
            assert result["organization_id"] == str(organization_with_twilio_number.id)
            mock_handler.assert_called_once()

    async def test_customer_message_to_provisioned_number_routes_to_customer_flow(
        self, db, mock_whatsapp_client, organization_with_staff
    ):
        """End customer message routes to customer flow (Case 5)."""
        org, staff, location = organization_with_staff
        router = MessageRouter(db=db, whatsapp_client=mock_whatsapp_client)

        with patch(
            "app.services.customer_flows.CustomerFlowHandler.handle_message",
            new_callable=AsyncMock,
        ) as mock_handler:
            mock_handler.return_value = "¡Bienvenido a Barbería Don Pedro!"

            result = await router.route_message(
                phone_number_id=org.whatsapp_phone_number_id,
                sender_phone="+525566667777",  # Not staff, must be customer
                message_id="test_msg_005",
                message_content="Quiero agendar un corte",
                sender_name="New Customer",
            )

            assert result["case"] == "5"
            assert result["sender_type"] == "customer"
            assert result["organization_id"] == str(org.id)

    async def test_staff_message_to_provisioned_number_routes_to_business_management(
        self, db, mock_whatsapp_client, organization_with_staff
    ):
        """Staff message routes to business management (Case 4)."""
        org, staff, location = organization_with_staff

        # Mark staff as already having first message
        staff.first_message_at = "2024-01-01T00:00:00Z"
        await db.flush()

        router = MessageRouter(db=db, whatsapp_client=mock_whatsapp_client)

        with patch(
            "app.services.conversation.ConversationHandler.handle_staff_message",
            new_callable=AsyncMock,
        ) as mock_handler:
            mock_handler.return_value = "Aquí está tu agenda de hoy..."

            result = await router.route_message(
                phone_number_id=org.whatsapp_phone_number_id,
                sender_phone=staff.phone_number,  # Owner's phone
                message_id="test_msg_006",
                message_content="Mi agenda",
                sender_name="Pedro",
            )

            assert result["case"] == "4"
            assert result["sender_type"] == "staff"
            mock_handler.assert_called_once()

    async def test_unknown_number_routes_to_parlo_central(self, db, mock_whatsapp_client):
        """Message to unknown number (Parlo Central) triggers onboarding."""
        router = MessageRouter(db=db, whatsapp_client=mock_whatsapp_client)

        with patch.object(
            router, "_handle_business_onboarding", new_callable=AsyncMock
        ) as mock_handler:
            mock_handler.return_value = "¡Hola! Soy Parlo..."

            result = await router.route_message(
                phone_number_id="UNKNOWN_NUMBER_ID",  # Not in database
                sender_phone="+525511112222",
                message_id="test_msg_007",
                message_content="Hola",
                sender_name="Test User",
            )

            # Since org not found, should route to central number flow
            assert result["case"] == "1"
            assert result["route"] == "business_onboarding"


class TestMessageRouterDeduplication:
    """Tests for message deduplication."""

    async def test_duplicate_message_is_skipped(self, db, mock_whatsapp_client):
        """Duplicate message_id is not processed twice."""
        router = MessageRouter(db=db, whatsapp_client=mock_whatsapp_client)

        # First message
        with patch.object(
            router, "_handle_business_onboarding", new_callable=AsyncMock
        ) as mock_handler:
            mock_handler.return_value = "¡Hola!"

            result1 = await router.route_message(
                phone_number_id="PARLO_CENTRAL_ID",
                sender_phone="+525533334444",
                message_id="duplicate_msg_id",
                message_content="Hola",
            )
            await db.commit()

            assert result1["status"] == "success"
            assert mock_handler.call_count == 1

        # Same message_id again
        result2 = await router.route_message(
            phone_number_id="PARLO_CENTRAL_ID",
            sender_phone="+525533334444",
            message_id="duplicate_msg_id",  # Same ID
            message_content="Hola",
        )

        assert result2["status"] == "duplicate"


class TestMessageRouterWhatsAppResponse:
    """Tests for WhatsApp response sending."""

    async def test_sends_whatsapp_response(self, db, mock_whatsapp_client):
        """Response is sent via WhatsApp client."""
        router = MessageRouter(db=db, whatsapp_client=mock_whatsapp_client)

        with patch.object(
            router, "_handle_business_onboarding", new_callable=AsyncMock
        ) as mock_handler:
            mock_handler.return_value = "¡Hola! Soy Parlo..."

            await router.route_message(
                phone_number_id="PARLO_CENTRAL_ID",
                sender_phone="+525544445555",
                message_id="test_msg_008",
                message_content="Hola",
            )

            mock_whatsapp_client.send_text_message.assert_called_once_with(
                phone_number_id="PARLO_CENTRAL_ID",
                to="+525544445555",
                message="¡Hola! Soy Parlo...",
            )


class TestMessageRouterCompletedOnboarding:
    """Tests for handling completed onboarding."""

    async def test_redirects_active_org_to_business_management(self, db, mock_whatsapp_client):
        """Active organization redirects to business management."""
        from datetime import datetime

        # Create active organization with owner
        org = Organization(
            id=uuid4(),
            name="Test Business",
            phone_country_code="52",
            phone_number="+525577778888",
            whatsapp_phone_number_id="+525577778888",
            timezone="America/Mexico_City",
            status=OrganizationStatus.ACTIVE.value,
            onboarding_state=OnboardingState.COMPLETED,
            onboarding_data={},
            onboarding_conversation_context={},
        )
        db.add(org)
        await db.flush()

        location = Location(
            id=uuid4(),
            organization_id=org.id,
            name="Main",
            is_primary=True,
        )
        db.add(location)
        await db.flush()

        staff = Staff(
            id=uuid4(),
            organization_id=org.id,
            location_id=location.id,
            name="Owner",
            phone_number="+525577778888",
            role=StaffRole.OWNER.value,
            permission_level=ParloUserPermissionLevel.OWNER.value,
            is_active=True,
            first_message_at=datetime.now(UTC),
        )
        db.add(staff)
        await db.flush()

        router = MessageRouter(db=db, whatsapp_client=mock_whatsapp_client)

        with patch(
            "app.services.conversation.ConversationHandler.handle_staff_message",
            new_callable=AsyncMock,
        ) as mock_handler:
            mock_handler.return_value = "Tu agenda de hoy..."

            result = await router.route_message(
                phone_number_id="PARLO_CENTRAL_ID",
                sender_phone="+525577778888",
                message_id="test_msg_010",
                message_content="Mi agenda",
            )

            # Should route to business management since org is active
            # and user is registered as staff
            assert result["case"] == "2a"
            assert result["route"] == "business_management"

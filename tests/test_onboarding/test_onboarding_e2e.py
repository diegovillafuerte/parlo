"""End-to-end tests for onboarding flow with Twilio provisioning.

These tests verify the complete onboarding flow from first message
through organization activation and subsequent message routing.

Updated to use Organization-based onboarding (no OnboardingSession).
"""

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from app.models import (
    Location,
    OrganizationStatus,
    ParloUser,
    ParloUserRole,
)
from app.services.message_router import MessageRouter
from app.services.onboarding import OnboardingHandler, OnboardingState
from tests.test_onboarding.conftest import (
    verify_services_created,
    verify_staff_created,
)

# Aliases for readability
Staff = ParloUser
StaffRole = ParloUserRole

pytestmark = pytest.mark.asyncio


class TestOnboardingE2EWithTwilioProvisioning:
    """End-to-end tests including Twilio number provisioning."""

    async def test_complete_onboarding_with_twilio_number(self, db, mock_whatsapp_client):
        """
        Full flow:
        1. User texts Parlo Central: "Hola"
        2. Onboarding conversation collects business info + services
        3. User chooses Twilio provisioning
        4. Number provisioned (mocked Twilio API)
        5. Organization activated with whatsapp_phone_number_id = provisioned number
        6. Verify message to provisioned number routes to this org
        """
        handler = OnboardingHandler(db=db)

        # Step 1: Create organization
        org = await handler.get_or_create_organization(
            phone_number="+525599998888",
            sender_name="Roberto",
        )
        assert org.status == OrganizationStatus.ONBOARDING.value
        assert org.onboarding_state == OnboardingState.INITIATED

        # Step 2: Save business info
        await handler._execute_tool(
            org=org,
            tool_name="save_business_info",
            tool_input={
                "business_name": "Barbería El Patrón",
                "business_type": "barbershop",
                "owner_name": "Roberto García",
            },
        )
        await db.refresh(org)
        assert org.onboarding_state == OnboardingState.COLLECTING_SERVICES
        assert org.name == "Barbería El Patrón"

        # Step 3: Add services
        await handler._execute_tool(
            org=org,
            tool_name="add_service",
            tool_input={"name": "Corte clásico", "duration_minutes": 30, "price": 120},
        )
        await handler._execute_tool(
            org=org,
            tool_name="add_service",
            tool_input={"name": "Corte y barba", "duration_minutes": 45, "price": 180},
        )

        # Step 4: Provision Twilio number
        with patch(
            "app.services.onboarding.provision_number_for_business",
            new_callable=AsyncMock,
        ) as mock_provision:
            mock_provision.return_value = {
                "phone_number": "+525588887777",
                "phone_number_sid": "PN_ROBERTO_001",
                "friendly_name": "Parlo - Barbería El Patrón",
            }

            result = await handler._execute_tool(
                org=org,
                tool_name="provision_twilio_number",
                tool_input={"country_code": "MX"},
            )

            assert result["success"] is True
            assert result["phone_number"] == "+525588887777"

            mock_provision.assert_called_once_with(
                business_name="Barbería El Patrón",
                webhook_base_url=pytest.approx(mock_provision.call_args[1]["webhook_base_url"]),
                country_code="MX",
            )

        # Step 5: Complete onboarding
        result = await handler._execute_tool(
            org=org,
            tool_name="complete_onboarding",
            tool_input={"confirmed": True},
        )

        assert result["success"] is True

        # Verify organization is now active
        await db.refresh(org)
        assert org.status == OrganizationStatus.ACTIVE.value
        assert org.whatsapp_phone_number_id == "+525588887777"

        # Verify services were created
        services = await verify_services_created(db, org.id, expected_count=2)
        assert any(s.name == "Corte clásico" for s in services)
        assert any(s.name == "Corte y barba" for s in services)

        # Verify owner staff is linked to services
        owner = await verify_staff_created(
            db,
            organization_id=org.id,
            phone_number="+525599998888",
            expected_name="Roberto García",
            expected_role=StaffRole.OWNER.value,
        )
        assert len(owner.service_types) == 2

        # Step 6: Verify routing - message to provisioned number finds this org
        router = MessageRouter(db=db, whatsapp_client=mock_whatsapp_client)

        with patch(
            "app.services.customer_flows.CustomerFlowHandler.handle_message",
            new_callable=AsyncMock,
        ) as mock_handler:
            mock_handler.return_value = "¡Bienvenido a Barbería El Patrón!"

            result = await router.route_message(
                phone_number_id="+525588887777",  # The provisioned number
                sender_phone="+525511112222",  # A customer
                message_id="test_route_001",
                message_content="Quiero una cita",
                sender_name="Customer",
            )

            assert result["status"] == "success"
            assert result["organization_id"] == str(org.id)
            assert result["case"] == "5"  # End customer

    async def test_onboarding_creates_org_immediately(self, db, mock_whatsapp_client):
        """First message creates Organization with ONBOARDING status."""
        handler = OnboardingHandler(db=db)

        # New user messages Parlo
        org = await handler.get_or_create_organization(
            phone_number="+525577778888",
            sender_name="Test User",
        )

        # Verify organization was created immediately
        assert org is not None
        assert org.status == OrganizationStatus.ONBOARDING.value
        assert org.onboarding_state == OnboardingState.INITIATED

        # Verify staff (owner) was created
        result = await db.execute(
            select(Staff).where(
                Staff.organization_id == org.id,
                Staff.phone_number == "+525577778888",
            )
        )
        staff = result.scalar_one_or_none()
        assert staff is not None
        assert staff.role == StaffRole.OWNER.value

        # Verify location was created
        result = await db.execute(
            select(Location).where(
                Location.organization_id == org.id,
                Location.is_primary == True,
            )
        )
        location = result.scalar_one_or_none()
        assert location is not None
        assert location.name == "Principal"

    async def test_returning_user_continues_onboarding(self, db, mock_whatsapp_client):
        """Returning user with ONBOARDING org continues where they left off."""
        handler = OnboardingHandler(db=db)

        # First message
        org = await handler.get_or_create_organization(
            phone_number="+525566667777",
            sender_name="Maria",
        )

        # Save some business info
        await handler._execute_tool(
            org=org,
            tool_name="save_business_info",
            tool_input={
                "business_name": "Salón Maria",
                "business_type": "salon",
                "owner_name": "Maria",
            },
        )

        await db.commit()

        # New handler instance (simulating new request)
        handler2 = OnboardingHandler(db=db)

        # Get or create should return the same org
        org2 = await handler2.get_or_create_organization(
            phone_number="+525566667777",
            sender_name="Maria",
        )

        assert org2.id == org.id
        assert org2.onboarding_state == OnboardingState.COLLECTING_SERVICES
        assert org2.onboarding_data["business_name"] == "Salón Maria"


class TestOrganizationDeletionCleansUp:
    """Tests that deleting organization cleans up properly."""

    async def test_delete_org_allows_fresh_onboarding(self, db, mock_whatsapp_client):
        """After deleting org, same phone can start fresh onboarding."""
        handler = OnboardingHandler(db=db)

        # Create and complete onboarding
        org = await handler.get_or_create_organization(
            phone_number="+525544443333",
            sender_name="Pedro",
        )
        org_id = org.id

        await handler._execute_tool(
            org=org,
            tool_name="save_business_info",
            tool_input={
                "business_name": "Barbería Pedro",
                "business_type": "barbershop",
                "owner_name": "Pedro",
            },
        )
        await handler._execute_tool(
            org=org,
            tool_name="add_service",
            tool_input={"name": "Corte", "duration_minutes": 30, "price": 100},
        )
        await handler._execute_tool(
            org=org,
            tool_name="complete_onboarding",
            tool_input={"confirmed": True},
        )

        await db.commit()

        # Delete organization
        from app.services.admin import delete_organization

        deleted = await delete_organization(db, org_id)
        assert deleted is True

        # Now the same phone should be able to start fresh
        handler2 = OnboardingHandler(db=db)
        new_org = await handler2.get_or_create_organization(
            phone_number="+525544443333",
            sender_name="Pedro",
        )

        # Should be a NEW organization
        assert new_org.id != org_id
        assert new_org.status == OrganizationStatus.ONBOARDING.value
        assert new_org.onboarding_state == OnboardingState.INITIATED

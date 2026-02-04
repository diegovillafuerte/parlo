"""Unit tests for onboarding tool execution.

Tests individual tools in the OnboardingHandler._execute_tool method.
Updated to use Organization-based onboarding (no OnboardingSession).
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.models import Organization, OrganizationStatus
from app.services.onboarding import OnboardingHandler, OnboardingState


pytestmark = pytest.mark.asyncio


class TestSaveBusinessInfoTool:
    """Tests for save_business_info tool."""

    async def test_saves_basic_business_info(
        self, db, onboarding_session_initiated
    ):
        """save_business_info stores business name, type, and owner."""
        org = onboarding_session_initiated  # This is now an Organization
        handler = OnboardingHandler(db=db)

        result = await handler._execute_tool(
            org=org,
            tool_name="save_business_info",
            tool_input={
                "business_name": "Salón Bella",
                "business_type": "salon",
                "owner_name": "Maria García",
            },
        )

        assert result["success"] is True
        assert result["business_name"] == "Salón Bella"
        assert result["owner_name"] == "Maria García"

        # Verify data was stored in org.onboarding_data
        await db.refresh(org)
        assert org.onboarding_data["business_name"] == "Salón Bella"
        assert org.onboarding_data["business_type"] == "salon"
        assert org.onboarding_data["owner_name"] == "Maria García"
        # Also verify org.name was updated
        assert org.name == "Salón Bella"

    async def test_saves_optional_address_and_city(
        self, db, onboarding_session_initiated
    ):
        """save_business_info stores optional address and city."""
        org = onboarding_session_initiated
        handler = OnboardingHandler(db=db)

        result = await handler._execute_tool(
            org=org,
            tool_name="save_business_info",
            tool_input={
                "business_name": "Barbería Don Carlos",
                "business_type": "barbershop",
                "owner_name": "Carlos Rodríguez",
                "address": "Av. Reforma 123",
                "city": "CDMX",
            },
        )

        assert result["success"] is True

        await db.refresh(org)
        assert org.onboarding_data["address"] == "Av. Reforma 123"
        assert org.onboarding_data["city"] == "CDMX"

    async def test_transitions_state_to_collecting_services(
        self, db, onboarding_session_initiated
    ):
        """save_business_info transitions state to COLLECTING_SERVICES."""
        org = onboarding_session_initiated
        handler = OnboardingHandler(db=db)

        await handler._execute_tool(
            org=org,
            tool_name="save_business_info",
            tool_input={
                "business_name": "Spa Zen",
                "business_type": "spa",
                "owner_name": "Ana López",
            },
        )

        await db.refresh(org)
        assert org.onboarding_state == OnboardingState.COLLECTING_SERVICES


class TestAddServiceTool:
    """Tests for add_service tool."""

    async def test_adds_first_service(
        self, db, onboarding_session_collecting_services
    ):
        """add_service creates services array and adds first service."""
        org = onboarding_session_collecting_services
        handler = OnboardingHandler(db=db)

        result = await handler._execute_tool(
            org=org,
            tool_name="add_service",
            tool_input={
                "name": "Corte de cabello",
                "duration_minutes": 30,
                "price": 150,
            },
        )

        assert result["success"] is True
        assert result["total_services"] == 1
        assert "Corte de cabello" in result["menu_display"]

        await db.refresh(org)
        assert len(org.onboarding_data["services"]) == 1
        assert org.onboarding_data["services"][0]["name"] == "Corte de cabello"

    async def test_adds_multiple_services(
        self, db, onboarding_session_collecting_services
    ):
        """add_service accumulates services."""
        org = onboarding_session_collecting_services
        handler = OnboardingHandler(db=db)

        # Add first service
        await handler._execute_tool(
            org=org,
            tool_name="add_service",
            tool_input={"name": "Corte", "duration_minutes": 30, "price": 100},
        )

        # Add second service
        result = await handler._execute_tool(
            org=org,
            tool_name="add_service",
            tool_input={"name": "Tinte", "duration_minutes": 90, "price": 500},
        )

        assert result["total_services"] == 2

        await db.refresh(org)
        assert len(org.onboarding_data["services"]) == 2


class TestCompleteOnboardingTool:
    """Tests for complete_onboarding tool."""

    async def test_activates_organization_on_completion(
        self, db, onboarding_org_ready_for_completion
    ):
        """complete_onboarding activates organization and creates services."""
        org = onboarding_org_ready_for_completion
        handler = OnboardingHandler(db=db)

        result = await handler._execute_tool(
            org=org,
            tool_name="complete_onboarding",
            tool_input={"confirmed": True},
        )

        assert result["success"] is True
        assert result["organization_id"] == str(org.id)

        await db.refresh(org)
        assert org.status == OrganizationStatus.ACTIVE.value
        assert org.onboarding_state == OnboardingState.COMPLETED

    async def test_requires_confirmation(
        self, db, onboarding_org_ready_for_completion
    ):
        """complete_onboarding requires confirmed=True."""
        org = onboarding_org_ready_for_completion
        handler = OnboardingHandler(db=db)

        result = await handler._execute_tool(
            org=org,
            tool_name="complete_onboarding",
            tool_input={"confirmed": False},
        )

        assert result["success"] is False

        await db.refresh(org)
        assert org.status == OrganizationStatus.ONBOARDING.value

    async def test_requires_business_name(
        self, db, onboarding_session_initiated
    ):
        """complete_onboarding fails without business name."""
        org = onboarding_session_initiated
        handler = OnboardingHandler(db=db)

        result = await handler._execute_tool(
            org=org,
            tool_name="complete_onboarding",
            tool_input={"confirmed": True},
        )

        assert result["success"] is False
        assert "nombre del negocio" in result["error"].lower()

    async def test_requires_at_least_one_service(
        self, db, onboarding_session_collecting_services
    ):
        """complete_onboarding fails without services."""
        org = onboarding_session_collecting_services
        handler = OnboardingHandler(db=db)

        result = await handler._execute_tool(
            org=org,
            tool_name="complete_onboarding",
            tool_input={"confirmed": True},
        )

        assert result["success"] is False
        assert "servicio" in result["error"].lower()


class TestProvisionTwilioNumberTool:
    """Tests for provision_twilio_number tool."""

    async def test_provisions_twilio_number(
        self, db, onboarding_org_with_services
    ):
        """provision_twilio_number stores provisioned number in onboarding_data."""
        org = onboarding_org_with_services
        handler = OnboardingHandler(db=db)

        with patch(
            "app.services.onboarding.provision_number_for_business",
            new_callable=AsyncMock,
        ) as mock_provision:
            mock_provision.return_value = {
                "phone_number": "+525588887777",
                "phone_number_sid": "PN_TEST_001",
                "friendly_name": "Yume - Barbería Don Juan",
            }

            result = await handler._execute_tool(
                org=org,
                tool_name="provision_twilio_number",
                tool_input={"country_code": "MX"},
            )

            assert result["success"] is True
            assert result["phone_number"] == "+525588887777"

            await db.refresh(org)
            assert org.onboarding_data["twilio_provisioned_number"] == "+525588887777"
            assert org.onboarding_data["twilio_phone_number_sid"] == "PN_TEST_001"

    async def test_requires_business_name_before_provisioning(
        self, db, onboarding_session_initiated
    ):
        """provision_twilio_number fails without business name."""
        org = onboarding_session_initiated
        handler = OnboardingHandler(db=db)

        result = await handler._execute_tool(
            org=org,
            tool_name="provision_twilio_number",
            tool_input={"country_code": "MX"},
        )

        assert result["success"] is False
        assert "nombre del negocio" in result["error"].lower()

"""Twilio number provisioning service.

This service handles provisioning dedicated WhatsApp numbers for businesses.
Following the PRD's hybrid approach:
1. Business completes onboarding via Yume's main number
2. We provision a dedicated Twilio number for their customers
3. (Future) Option to migrate their existing number

Note: Twilio WhatsApp number provisioning requires:
- Purchasing a phone number from Twilio
- Registering it with WhatsApp Business
- Configuring webhook URLs
"""

import logging
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class TwilioProvisioningError(Exception):
    """Error during Twilio provisioning."""
    pass


class TwilioProvisioningService:
    """Service for provisioning Twilio WhatsApp numbers."""

    def __init__(self):
        """Initialize Twilio provisioning service."""
        self.account_sid = settings.twilio_account_sid
        self.auth_token = settings.twilio_auth_token
        self.base_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}"
        self.client = httpx.AsyncClient(timeout=30.0)

    @property
    def is_configured(self) -> bool:
        """Check if Twilio is properly configured."""
        return bool(self.account_sid and self.auth_token)

    async def list_available_numbers(
        self,
        country_code: str = "MX",
        area_code: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """List available phone numbers for purchase.

        Args:
            country_code: ISO country code (default: MX for Mexico)
            area_code: Optional area code filter
            limit: Max numbers to return

        Returns:
            List of available phone numbers with pricing
        """
        if not self.is_configured:
            logger.warning("Twilio not configured, returning empty list")
            return []

        url = f"{self.base_url}/AvailablePhoneNumbers/{country_code}/Mobile.json"
        params = {"PageSize": limit}
        if area_code:
            params["AreaCode"] = area_code

        try:
            response = await self.client.get(
                url,
                params=params,
                auth=(self.account_sid, self.auth_token),
            )
            response.raise_for_status()
            data = response.json()
            return data.get("available_phone_numbers", [])
        except httpx.HTTPError as e:
            logger.error(f"Failed to list available numbers: {e}")
            return []

    async def purchase_number(
        self,
        phone_number: str,
        friendly_name: str | None = None,
        webhook_url: str | None = None,
    ) -> dict[str, Any] | None:
        """Purchase a phone number from Twilio.

        Args:
            phone_number: Phone number to purchase (E.164 format)
            friendly_name: Human-readable name for the number
            webhook_url: URL for incoming message webhooks

        Returns:
            Purchased number details or None on failure
        """
        if not self.is_configured:
            logger.warning("Twilio not configured, cannot purchase number")
            return None

        url = f"{self.base_url}/IncomingPhoneNumbers.json"
        data = {"PhoneNumber": phone_number}

        if friendly_name:
            data["FriendlyName"] = friendly_name
        if webhook_url:
            data["SmsUrl"] = webhook_url

        try:
            response = await self.client.post(
                url,
                data=data,
                auth=(self.account_sid, self.auth_token),
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to purchase number: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return None

    async def configure_webhook(
        self,
        phone_number_sid: str,
        webhook_url: str,
    ) -> bool:
        """Configure webhook URL for a phone number.

        Args:
            phone_number_sid: Twilio phone number SID
            webhook_url: URL for incoming message webhooks

        Returns:
            True if successful
        """
        if not self.is_configured:
            return False

        url = f"{self.base_url}/IncomingPhoneNumbers/{phone_number_sid}.json"
        data = {"SmsUrl": webhook_url}

        try:
            response = await self.client.post(
                url,
                data=data,
                auth=(self.account_sid, self.auth_token),
            )
            response.raise_for_status()
            return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to configure webhook: {e}")
            return False

    async def release_number(self, phone_number_sid: str) -> bool:
        """Release (delete) a phone number.

        Args:
            phone_number_sid: Twilio phone number SID

        Returns:
            True if successful
        """
        if not self.is_configured:
            return False

        url = f"{self.base_url}/IncomingPhoneNumbers/{phone_number_sid}.json"

        try:
            response = await self.client.delete(
                url,
                auth=(self.account_sid, self.auth_token),
            )
            response.raise_for_status()
            return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to release number: {e}")
            return False

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()


async def provision_number_for_business(
    business_name: str,
    webhook_base_url: str,
    country_code: str = "MX",
) -> dict[str, Any] | None:
    """Provision a new phone number for a business.

    This is a convenience function that:
    1. Lists available numbers
    2. Purchases the first available one
    3. Configures the webhook

    Args:
        business_name: Name of the business (for friendly name)
        webhook_base_url: Base URL for webhooks (e.g., https://api.yume.mx)
        country_code: Country code for the number

    Returns:
        Dict with phone_number, phone_number_sid, or None on failure
    """
    service = TwilioProvisioningService()

    try:
        # List available numbers
        available = await service.list_available_numbers(
            country_code=country_code,
            limit=1,
        )

        if not available:
            logger.error("No phone numbers available")
            return None

        # Purchase the first available
        number_to_buy = available[0]["phone_number"]
        purchased = await service.purchase_number(
            phone_number=number_to_buy,
            friendly_name=f"Yume - {business_name}",
            webhook_url=f"{webhook_base_url}/api/v1/webhooks/whatsapp",
        )

        if not purchased:
            logger.error("Failed to purchase number")
            return None

        return {
            "phone_number": purchased["phone_number"],
            "phone_number_sid": purchased["sid"],
            "friendly_name": purchased.get("friendly_name"),
        }

    finally:
        await service.close()

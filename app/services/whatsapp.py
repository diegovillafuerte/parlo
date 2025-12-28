"""WhatsApp API client - handles sending messages to Meta's Cloud API."""

import logging
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class WhatsAppClient:
    """Client for Meta WhatsApp Cloud API."""

    def __init__(self, mock_mode: bool = True):
        """Initialize WhatsApp client.

        Args:
            mock_mode: If True, don't actually call Meta API (for testing)
        """
        self.mock_mode = mock_mode
        self.base_url = f"https://graph.facebook.com/{settings.meta_api_version}"
        self.client = httpx.AsyncClient(timeout=30.0)

    async def send_text_message(
        self, phone_number_id: str, to: str, message: str
    ) -> dict[str, Any]:
        """Send a text message via WhatsApp.

        Args:
            phone_number_id: Our WhatsApp phone number ID (from Meta)
            to: Recipient's phone number
            message: Message content

        Returns:
            Response from Meta API (or mock response)
        """
        if self.mock_mode:
            logger.info(
                f"📱 [MOCK] Sending WhatsApp message:\n"
                f"  From: {phone_number_id}\n"
                f"  To: {to}\n"
                f"  Message: {message}"
            )
            return {
                "messaging_product": "whatsapp",
                "contacts": [{"input": to, "wa_id": to}],
                "messages": [{"id": f"mock_msg_{to}"}],
            }

        # Real API call
        url = f"{self.base_url}/{phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {settings.meta_access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"body": message},
        }

        try:
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            logger.info(f"✅ Sent WhatsApp message to {to}")
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"❌ Failed to send WhatsApp message: {e}")
            raise

    async def send_template_message(
        self,
        phone_number_id: str,
        to: str,
        template_name: str,
        language_code: str = "es_MX",
        components: list[dict] | None = None,
    ) -> dict[str, Any]:
        """Send a template message via WhatsApp.

        Template messages are used for notifications outside the 24-hour window.

        Args:
            phone_number_id: Our WhatsApp phone number ID
            to: Recipient's phone number
            template_name: Name of approved template
            language_code: Language code (default: es_MX for Mexican Spanish)
            components: Template parameters

        Returns:
            Response from Meta API (or mock response)
        """
        if self.mock_mode:
            logger.info(
                f"📱 [MOCK] Sending WhatsApp template:\n"
                f"  From: {phone_number_id}\n"
                f"  To: {to}\n"
                f"  Template: {template_name}\n"
                f"  Components: {components}"
            )
            return {
                "messaging_product": "whatsapp",
                "contacts": [{"input": to, "wa_id": to}],
                "messages": [{"id": f"mock_template_{to}"}],
            }

        # Real API call
        url = f"{self.base_url}/{phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {settings.meta_access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
                "components": components or [],
            },
        }

        try:
            response = await self.client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            logger.info(f"✅ Sent WhatsApp template '{template_name}' to {to}")
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"❌ Failed to send WhatsApp template: {e}")
            raise

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

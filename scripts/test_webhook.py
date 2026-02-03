"""Test utility to simulate WhatsApp webhook calls.

This script helps you test the message router locally without needing
actual WhatsApp credentials or ngrok.

Usage:
    # Test Meta webhook verification (GET request)
    python scripts/test_webhook.py --verify --meta

    # Test Meta message webhook (POST request)
    python scripts/test_webhook.py --customer "Hola" --meta
    python scripts/test_webhook.py --staff "Qué tengo hoy?" --meta

    # Test Twilio webhook (POST request - form data)
    python scripts/test_webhook.py --customer "Hola" --twilio
    python scripts/test_webhook.py --staff "Qué tengo hoy?" --twilio

    # Default is Meta format
    python scripts/test_webhook.py --customer "Hola"
"""

import asyncio
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx

# Load settings to get verify token
from app.config import get_settings

settings = get_settings()

BASE_URL = "http://localhost:8000/api/v1/webhooks"


async def send_meta_webhook(
    message: str,
    phone_number_id: str = "test_phone_123",
    sender_phone: str = "525587654321",
    sender_name: str = "Test User",
):
    """Send a test webhook in Meta Cloud API format.

    Args:
        message: Message content to send
        phone_number_id: Business's WhatsApp phone number ID
        sender_phone: Sender's phone number
        sender_name: Sender's name
    """
    # Ensure phone doesn't have + prefix for Meta format
    sender_phone_clean = sender_phone.lstrip("+")

    # Meta's webhook payload format
    webhook_payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WABA_ID_123",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "phone_number_id": phone_number_id,
                                "display_phone_number": "+525512345678",
                            },
                            "contacts": [
                                {
                                    "wa_id": sender_phone_clean,
                                    "profile": {"name": sender_name},
                                }
                            ],
                            "messages": [
                                {
                                    "from": sender_phone_clean,
                                    "id": f"wamid_test_{int(time.time() * 1000)}",
                                    "timestamp": str(int(time.time())),
                                    "type": "text",
                                    "text": {"body": message},
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/whatsapp/meta",
                json=webhook_payload,
                timeout=30.0,
            )
            response.raise_for_status()
            print(f"✅ Meta webhook sent successfully")
            print(f"Response: {response.json()}")
        except httpx.HTTPError as e:
            print(f"❌ Error: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"Response: {e.response.text}")


async def send_twilio_webhook(
    message: str,
    to_number: str = "+14155238886",  # Yume's Twilio number
    sender_phone: str = "+525587654321",
    sender_name: str = "Test User",
):
    """Send a test webhook in Twilio format (form-encoded).

    Args:
        message: Message content to send
        to_number: Yume's Twilio WhatsApp number (To field)
        sender_phone: Sender's phone number
        sender_name: Sender's name
    """
    # Twilio sends form-encoded data
    form_data = {
        "MessageSid": f"SM_test_{int(time.time() * 1000)}",
        "From": f"whatsapp:{sender_phone}",
        "To": f"whatsapp:{to_number}",
        "Body": message,
        "ProfileName": sender_name,
        "NumMedia": "0",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{BASE_URL}/whatsapp",
                data=form_data,
                timeout=30.0,
            )
            response.raise_for_status()
            print(f"✅ Twilio webhook sent successfully")
            print(f"Response: {response.text[:200]}")
        except httpx.HTTPError as e:
            print(f"❌ Error: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"Response: {e.response.text}")


async def test_meta_verification():
    """Test Meta webhook verification (GET request).

    This simulates what Meta does when you register your webhook URL.
    """
    print("\n" + "=" * 80)
    print("🔍 Testing META WEBHOOK VERIFICATION (GET)")
    print("=" * 80)

    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": settings.meta_webhook_verify_token,
        "hub.challenge": "test_challenge_response_123",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{BASE_URL}/whatsapp/meta",
                params=params,
                timeout=10.0,
            )

            if response.status_code == 200 and response.text == "test_challenge_response_123":
                print(f"✅ Webhook verification PASSED")
                print(f"   Challenge echoed back: {response.text}")
            else:
                print(f"❌ Webhook verification FAILED")
                print(f"   Status: {response.status_code}")
                print(f"   Expected: test_challenge_response_123")
                print(f"   Got: {response.text}")

        except httpx.HTTPError as e:
            print(f"❌ Error: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"Response: {e.response.text}")


async def test_twilio_status():
    """Test Twilio webhook status endpoint."""
    print("\n" + "=" * 80)
    print("🔍 Testing TWILIO WEBHOOK STATUS (GET)")
    print("=" * 80)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{BASE_URL}/whatsapp/status",
                timeout=10.0,
            )
            response.raise_for_status()
            print(f"✅ Twilio status: {response.json()}")
        except httpx.HTTPError as e:
            print(f"❌ Error: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"Response: {e.response.text}")


async def main():
    """Run test scenarios."""
    import argparse

    parser = argparse.ArgumentParser(description="Test WhatsApp webhook locally")
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Test webhook verification (GET request)",
    )
    parser.add_argument(
        "--customer",
        type=str,
        help="Send a customer message with the given text",
    )
    parser.add_argument(
        "--staff",
        type=str,
        help="Send a staff message with the given text",
    )
    parser.add_argument(
        "--phone",
        type=str,
        default="+525587654321",
        help="Sender phone number (default: +525587654321)",
    )
    parser.add_argument(
        "--name",
        type=str,
        default="Test User",
        help="Sender name (default: Test User)",
    )
    parser.add_argument(
        "--phone-number-id",
        type=str,
        default="test_phone_123",
        help="Business phone number ID for Meta format (default: test_phone_123)",
    )
    parser.add_argument(
        "--meta",
        action="store_true",
        default=True,
        help="Use Meta Cloud API format (default)",
    )
    parser.add_argument(
        "--twilio",
        action="store_true",
        help="Use Twilio format instead of Meta",
    )

    args = parser.parse_args()

    # Determine format
    use_twilio = args.twilio

    if args.verify:
        if use_twilio:
            await test_twilio_status()
        else:
            await test_meta_verification()
    elif args.customer or args.staff:
        message = args.customer or args.staff
        print("\n" + "=" * 80)
        print(f"{'🟢 CUSTOMER' if args.customer else '🔵 STAFF'} message via {'TWILIO' if use_twilio else 'META'}")
        print("=" * 80)
        print(f"Phone: {args.phone}")
        print(f"Name: {args.name}")
        print(f"Message: {message}")
        print("=" * 80)

        if use_twilio:
            await send_twilio_webhook(
                message=message,
                sender_phone=args.phone,
                sender_name=args.name,
            )
        else:
            await send_meta_webhook(
                message=message,
                phone_number_id=args.phone_number_id,
                sender_phone=args.phone,
                sender_name=args.name,
            )
    else:
        # Run verification tests for both
        await test_meta_verification()
        await asyncio.sleep(0.5)
        await test_twilio_status()


if __name__ == "__main__":
    asyncio.run(main())

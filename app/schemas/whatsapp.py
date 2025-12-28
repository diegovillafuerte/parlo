"""Pydantic schemas for WhatsApp webhook payloads."""

from pydantic import BaseModel, Field


# Incoming webhook schemas (from Meta)
class WhatsAppProfile(BaseModel):
    """WhatsApp profile information."""

    name: str


class WhatsAppContact(BaseModel):
    """WhatsApp contact information."""

    wa_id: str = Field(..., description="WhatsApp ID (phone number)")
    profile: WhatsAppProfile


class WhatsAppTextMessage(BaseModel):
    """Text message content."""

    body: str


class WhatsAppMessage(BaseModel):
    """WhatsApp message from webhook."""

    from_: str = Field(..., alias="from", description="Sender's phone number")
    id: str = Field(..., description="Message ID (for deduplication)")
    timestamp: str
    type: str  # text, image, audio, etc.
    text: WhatsAppTextMessage | None = None
    # TODO: Add image, audio, etc. when needed


class WhatsAppMetadata(BaseModel):
    """Metadata about the WhatsApp number receiving the message."""

    phone_number_id: str = Field(..., description="Our WhatsApp phone number ID")
    display_phone_number: str


class WhatsAppValue(BaseModel):
    """Value object containing messages and metadata."""

    messaging_product: str
    metadata: WhatsAppMetadata
    contacts: list[WhatsAppContact] | None = None
    messages: list[WhatsAppMessage] | None = None


class WhatsAppChange(BaseModel):
    """Change object in webhook."""

    field: str
    value: WhatsAppValue


class WhatsAppEntry(BaseModel):
    """Entry object in webhook."""

    id: str = Field(..., description="WhatsApp Business Account ID")
    changes: list[WhatsAppChange]


class WhatsAppWebhook(BaseModel):
    """Complete WhatsApp webhook payload from Meta."""

    object: str  # "whatsapp_business_account"
    entry: list[WhatsAppEntry]


# Outgoing message schemas (to Meta)
class WhatsAppTextPayload(BaseModel):
    """Payload for sending a text message."""

    messaging_product: str = "whatsapp"
    recipient_type: str = "individual"
    to: str = Field(..., description="Recipient phone number")
    type: str = "text"
    text: dict[str, str] = Field(..., description="{'body': 'message content'}")


class WhatsAppTemplateParameter(BaseModel):
    """Template parameter."""

    type: str  # text, currency, date_time
    text: str | None = None


class WhatsAppTemplateComponent(BaseModel):
    """Template component."""

    type: str  # header, body, button
    parameters: list[WhatsAppTemplateParameter]


class WhatsAppTemplatePayload(BaseModel):
    """Payload for sending a template message."""

    messaging_product: str = "whatsapp"
    recipient_type: str = "individual"
    to: str = Field(..., description="Recipient phone number")
    type: str = "template"
    template: dict = Field(..., description="Template configuration")

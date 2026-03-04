"""Onboarding service - handles business registration via WhatsApp conversation.

This service manages the conversational onboarding flow where a business owner
can set up their Parlo account by chatting with the AI assistant.

Architecture (as of Feb 2026):
- Organization is created immediately on first message with status=ONBOARDING
- Onboarding progress is tracked in Organization.onboarding_state
- Collected data stored in Organization.onboarding_data
- Conversation history stored in Message table (NOT JSONB) to prevent race conditions
- When complete, Organization.status changes to ACTIVE

Flow:
1. User texts Parlo's main number
2. System detects they're not associated with any organization
3. Organization created with status=ONBOARDING, owner Staff created immediately
4. Onboarding flow begins, collecting:
   - Business name and type
   - Owner name (if not from WhatsApp profile)
   - Services offered (name, duration, price)
   - Business hours
5. complete_onboarding changes Organization.status to ACTIVE and creates ServiceTypes/Spots
"""

import logging
from datetime import UTC, datetime
from datetime import time as dt_time
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.client import OpenAIClient, get_openai_client
from app.config import get_settings
from app.models import (
    Availability,
    AvailabilityType,
    Conversation,
    ConversationStatus,
    Location,
    Message,
    MessageContentType,
    MessageDirection,
    MessageSenderType,
    Organization,
    OrganizationStatus,
    ParloUserPermissionLevel,
    ServiceType,
    Spot,
    Staff,
    StaffRole,
)
from app.services.ai_handler_base import ToolCallingMixin
from app.services.tracing import traced
from app.services.twilio_provisioning import provision_number_for_business
from app.utils.phone import normalize_phone_number

logger = logging.getLogger(__name__)


# Onboarding states (stored in Organization.onboarding_state)
class OnboardingState:
    """Onboarding progress states.

    State machine flow:
    1. INITIATED - Just started, no data collected yet
    2. COLLECTING_BUSINESS_INFO - Getting name, type, owner info
    3. COLLECTING_SERVICES - Getting services offered
    4. COLLECTING_HOURS - Getting business hours (optional)
    5. CONFIRMING - Showing summary, waiting for confirmation
    6. COMPLETED - Organization activated, done
    7. ABANDONED - User stopped responding (stores last_active_state in onboarding_data)
    """

    INITIATED = "initiated"
    COLLECTING_BUSINESS_INFO = "collecting_business_info"
    COLLECTING_SERVICES = "collecting_services"
    COLLECTING_HOURS = "collecting_hours"
    CONFIRMING = "confirming"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


# Default business hours for Mexican businesses
DEFAULT_BUSINESS_HOURS = {
    "monday": {"open": "09:00", "close": "19:00"},
    "tuesday": {"open": "09:00", "close": "19:00"},
    "wednesday": {"open": "09:00", "close": "19:00"},
    "thursday": {"open": "09:00", "close": "19:00"},
    "friday": {"open": "09:00", "close": "19:00"},
    "saturday": {"open": "09:00", "close": "17:00"},
    "sunday": {"closed": True},
}

DAY_NAME_TO_WEEKDAY = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


# Get frontend URL from config
_settings = get_settings()

# AI Tools for onboarding
ONBOARDING_TOOLS = [
    {
        "name": "save_business_info",
        "description": "Guarda la información básica del negocio cuando el usuario la proporciona.",
        "input_schema": {
            "type": "object",
            "properties": {
                "business_name": {
                    "type": "string",
                    "description": "Nombre del negocio (ej: 'Barbería Don Carlos', 'Salón Bella')",
                },
                "business_type": {
                    "type": "string",
                    "enum": ["salon", "barbershop", "spa", "nails", "other"],
                    "description": "Tipo de negocio",
                },
                "owner_name": {
                    "type": "string",
                    "description": "Nombre del dueño",
                },
                "address": {
                    "type": "string",
                    "description": "Dirección del negocio (opcional)",
                },
                "city": {
                    "type": "string",
                    "description": "Ciudad (opcional)",
                },
            },
            "required": ["business_name", "business_type", "owner_name"],
        },
    },
    {
        "name": "add_service",
        "description": "Agrega un servicio que ofrece el negocio. Llama esta herramienta por cada servicio que el usuario mencione. Después de llamar esta herramienta, SIEMPRE muestra al usuario su menú actualizado.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Nombre del servicio (ej: 'Corte de cabello', 'Manicure')",
                },
                "duration_minutes": {
                    "type": "integer",
                    "description": "Duración en minutos (ej: 30, 45, 60)",
                },
                "price": {
                    "type": "number",
                    "description": "Precio en pesos mexicanos (ej: 150, 200, 500)",
                },
            },
            "required": ["name", "duration_minutes", "price"],
        },
    },
    {
        "name": "remove_service",
        "description": "Elimina un servicio del menú. Úsalo cuando el usuario quiera quitar un servicio que se agregó por error.",
        "input_schema": {
            "type": "object",
            "properties": {
                "service_name": {
                    "type": "string",
                    "description": "Nombre del servicio a eliminar",
                },
            },
            "required": ["service_name"],
        },
    },
    {
        "name": "get_current_menu",
        "description": "Obtiene el menú de servicios actual para mostrarlo al usuario. Úsalo cuando necesites mostrar el menú completo.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "add_staff_member",
        "description": "Agrega un empleado al negocio. El dueño ya se registra automáticamente. Usa esto para agregar empleados adicionales.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Nombre del empleado",
                },
                "phone_number": {
                    "type": "string",
                    "description": "Número de WhatsApp del empleado (ej: 5512345678)",
                },
                "services": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Lista de nombres de servicios que hace este empleado. Si hace todos, omitir.",
                },
            },
            "required": ["name", "phone_number"],
        },
    },
    {
        "name": "save_business_hours",
        "description": "Guarda el horario de atención del negocio. Solo usa si el usuario proporciona horarios específicos.",
        "input_schema": {
            "type": "object",
            "properties": {
                "monday": {
                    "type": "object",
                    "properties": {
                        "open": {"type": "string"},
                        "close": {"type": "string"},
                        "closed": {"type": "boolean"},
                    },
                },
                "tuesday": {
                    "type": "object",
                    "properties": {
                        "open": {"type": "string"},
                        "close": {"type": "string"},
                        "closed": {"type": "boolean"},
                    },
                },
                "wednesday": {
                    "type": "object",
                    "properties": {
                        "open": {"type": "string"},
                        "close": {"type": "string"},
                        "closed": {"type": "boolean"},
                    },
                },
                "thursday": {
                    "type": "object",
                    "properties": {
                        "open": {"type": "string"},
                        "close": {"type": "string"},
                        "closed": {"type": "boolean"},
                    },
                },
                "friday": {
                    "type": "object",
                    "properties": {
                        "open": {"type": "string"},
                        "close": {"type": "string"},
                        "closed": {"type": "boolean"},
                    },
                },
                "saturday": {
                    "type": "object",
                    "properties": {
                        "open": {"type": "string"},
                        "close": {"type": "string"},
                        "closed": {"type": "boolean"},
                    },
                },
                "sunday": {
                    "type": "object",
                    "properties": {
                        "open": {"type": "string"},
                        "close": {"type": "string"},
                        "closed": {"type": "boolean"},
                    },
                },
            },
        },
    },
    {
        "name": "complete_onboarding",
        "description": "Finaliza el proceso de registro y crea la cuenta. Solo llama cuando: 1) tienes nombre del negocio, 2) al menos un servicio, 3) el usuario confirmó que está listo para activar su cuenta.",
        "input_schema": {
            "type": "object",
            "properties": {
                "confirmed": {
                    "type": "boolean",
                    "description": "True si el usuario confirmó que los datos son correctos",
                },
            },
            "required": ["confirmed"],
        },
    },
    {
        "name": "send_dashboard_link",
        "description": "Envía el link al dashboard y explica cómo iniciar sesión. Úsalo después de completar el registro.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "set_website_preference",
        "description": "Configura la preferencia de página web del negocio. El negocio puede tener una página web automática en [nombre].parlo.mx. Llama esta herramienta después de preguntar al usuario si quiere página web.",
        "input_schema": {
            "type": "object",
            "properties": {
                "wants_website": {
                    "type": "boolean",
                    "description": "True si el usuario quiere una página web, False si no",
                },
                "custom_slug": {
                    "type": "string",
                    "description": "Slug personalizado si el usuario quiere una dirección diferente a la sugerida. Solo letras minúsculas, números y guiones. Ejemplo: 'mi-barberia'",
                },
            },
            "required": ["wants_website"],
        },
    },
    {
        "name": "provision_twilio_number",
        "description": "Provisiona un nuevo número de WhatsApp dedicado para el negocio usando Twilio. Úsalo cuando el usuario NO tiene una cuenta de WhatsApp Business existente y quiere que Parlo le proporcione un número dedicado.",
        "input_schema": {
            "type": "object",
            "properties": {
                "country_code": {
                    "type": "string",
                    "description": "Código de país para el número (MX para México, US para Estados Unidos). Default: US",
                    "default": "US",
                },
            },
        },
    },
]


def _format_service_menu(services: list[dict]) -> str:
    """Format services list as a nice menu display.

    Args:
        services: List of service dicts with name, price, duration_minutes

    Returns:
        Formatted menu string
    """
    if not services:
        return "Sin servicios aún"

    lines = []
    for svc in services:
        lines.append(f"• {svc['name']} - ${svc['price']:.0f} ({svc['duration_minutes']} min)")
    return "\n".join(lines)


def build_onboarding_system_prompt(org: Organization) -> str:
    """Build the system prompt for onboarding conversations.

    Args:
        org: Organization being onboarded

    Returns:
        System prompt string
    """
    collected = org.onboarding_data or {}
    services = collected.get("services", [])
    staff_members = collected.get("staff", [])
    is_first_message = not collected.get("business_name") and not services

    # Build current progress summary
    progress_parts = []
    if collected.get("business_name"):
        progress_parts.append(f"• Negocio: {collected['business_name']}")
    if collected.get("owner_name"):
        progress_parts.append(f"• Dueño: {collected['owner_name']}")
    if collected.get("address"):
        progress_parts.append(f"• Dirección: {collected['address']}")
    if collected.get("business_hours"):
        progress_parts.append("• Horario: Configurado")
    if services:
        progress_parts.append(f"• Servicios: {len(services)}")
        for svc in services:
            progress_parts.append(
                f"  - {svc['name']} - ${svc['price']:.0f} ({svc['duration_minutes']} min)"
            )
    if staff_members:
        progress_parts.append(f"• Empleados adicionales: {len(staff_members)}")
        for st in staff_members:
            progress_parts.append(f"  - {st['name']} ({st.get('phone_number', 'sin tel')})")
    if collected.get("wants_website") is True:
        progress_parts.append(f"• Página web: {collected.get('website_slug', '?')}.parlo.mx")
    elif collected.get("wants_website") is False:
        progress_parts.append("• Página web: No quiere")

    progress = (
        "\n".join(progress_parts) if progress_parts else "Ninguna información recolectada aún."
    )

    # Build menu display for AI reference
    menu_display = _format_service_menu(services)

    # Determine current step
    if not collected.get("business_name"):
        current_step = "Paso 1: Obtener nombre del negocio y del dueño"
    elif not services:
        current_step = "Paso 2: Obtener servicios (nombre, precio, duración)"
    else:
        current_step = "Paso 3: Confirmar datos y activar cuenta"

    return f"""Eres Parlo, una asistente de inteligencia artificial que ayuda a negocios de belleza en México a automatizar sus citas por WhatsApp.

## IMPORTANTE: Primera Interacción
{"ESTA ES LA PRIMERA INTERACCIÓN. Debes presentarte con el mensaje de bienvenida completo." if is_first_message else "Ya te presentaste. Continúa con el flujo de registro."}

## Mensaje de Bienvenida (SOLO primera interacción)
Si es la primera interacción, responde EXACTAMENTE así:

"¡Hola! 👋 Soy Parlo, tu asistente para agendar citas automáticamente.

Ayudo a negocios de belleza a que sus clientes agenden por WhatsApp sin que tengas que contestar cada mensaje.

En unos minutos configuramos tu cuenta. Te voy a hacer unas preguntas sobre tu negocio.

¿Tienes un salón, barbería, o negocio de belleza?"

## Estado Actual del Registro
{progress}

## Menú de Servicios Actual
{menu_display}

## Paso Actual
{current_step}

## Flujo de Conversación

### Paso 1: Información del Negocio
- Pregunta primero si tienen un negocio de belleza
- Obtén: nombre del negocio, tipo (salon/barbershop/spa/nails), nombre del dueño
- Opcionalmente: dirección (útil para clientes)
- Usa herramienta `save_business_info` cuando tengas los datos básicos
- Después pregunta por los horarios de atención

### Paso 2: Horarios
- Pregunta qué días abren y en qué horario
- Ejemplo: "¿Qué días abren y en qué horario?"
- Si dan horario tipo "lunes a sábado de 10 a 8", usa `save_business_hours`
- Pregunta si cierran para comer o es horario corrido

### Paso 3: Servicios
- Pregunta qué servicios ofrecen con precio y duración
- Ejemplo: "Dime el nombre, cuánto dura y el precio. Ejemplo: 'Corte de cabello, 45 minutos, $150'"
- Por cada servicio mencionado, usa `add_service` INMEDIATAMENTE
- **IMPORTANTE**: Después de agregar servicios, MUESTRA el menú actualizado al usuario
- Formato: "Perfecto, registré N servicios:\n• Corte - $150 (30 min)\n• Barba - $100 (20 min)\n\n¿Falta algún servicio?"
- Pregunta si quieren agregar más servicios o si está completo

### Paso 4: Empleados (Opcional)
- Si tienen más de una persona, pregunta quién más atiende
- Para cada empleado necesitas: nombre y teléfono de WhatsApp
- Usa `add_staff_member` por cada empleado adicional
- Pregunta si todos hacen todos los servicios o hay especialidades
- El dueño ya se registra automáticamente con su número actual

### Paso 5: Página Web
- Ofrece al usuario una página web automática para su negocio
- Sugiere la dirección basada en el nombre del negocio (ej: "barberia-don-carlos.parlo.mx")
- Ejemplo: "También puedo crear una página web para tu negocio en barberia-don-carlos.parlo.mx donde tus clientes vean tus servicios, precios y horarios. ¿Te gustaría tenerla?"
- Si dicen sí con la dirección sugerida → usa `set_website_preference(wants_website=true)`
- Si quieren otra dirección → pregunta cuál, luego `set_website_preference(wants_website=true, custom_slug="...")`
- Si no quieren → `set_website_preference(wants_website=false)`
- IMPORTANTE: El slug debe ser solo letras minúsculas, números y guiones

### Paso 6: Confirmación y Activación
- Muestra un resumen de todo lo configurado
- Pregunta "¿Todo correcto? ¿Activamos tu cuenta?"
- Si confirman, usa `complete_onboarding` para crear la cuenta (esto también asigna automáticamente un número de WhatsApp)
- El resultado de `complete_onboarding` incluirá `whatsapp_number` (el número asignado) o `number_message` si queda pendiente
- Después usa `send_dashboard_link` para enviar el link al dashboard
- Incluye el número de WhatsApp asignado en el mensaje final al usuario

## ⚠️ CRÍTICO: Completar el Registro
**DEBES llamar la herramienta `complete_onboarding` cuando:**
1. Tienes el nombre del negocio guardado (save_business_info ya fue llamada)
2. Tienes al menos un servicio (add_service ya fue llamada al menos una vez)
3. El usuario confirma que está listo ("sí", "listo", "activa", "ok", "perfecto", "correcto", etc.)

**NO esperes a que el usuario diga palabras exactas.** Si ya tienes la información mínima y el usuario da cualquier señal de confirmación, LLAMA `complete_onboarding` con confirmed=true. Esta herramienta automáticamente asigna un número de WhatsApp, así que NO necesitas llamar `provision_twilio_number` por separado.

**Ejemplos de confirmación del usuario:**
- "Sí, activa" → LLAMA complete_onboarding
- "Ok, listo" → LLAMA complete_onboarding
- "Perfecto" → LLAMA complete_onboarding
- "Está bien" → LLAMA complete_onboarding
- "Dale" → LLAMA complete_onboarding
- "Va" → LLAMA complete_onboarding

**IMPORTANTE sobre el resultado de complete_onboarding:**
- Si `whatsapp_number` está presente → incluye ese número en tu mensaje al usuario
- Si solo `number_message` está presente → usa ese texto para informar sobre el número

## Instrucciones Importantes
- Habla en español mexicano natural, usa "tú" no "usted"
- Sé concisa pero amable. Máximo 3-4 oraciones por mensaje
- Cuando el usuario mencione servicios, USA LA HERRAMIENTA add_service inmediatamente
- Interpreta formatos flexibles de entrada:
  - "Corte dama $250 45 min" → Corte dama, 45 min, $250
  - "Corte 150" → Corte, duración estándar 30 min, $150
- Si el usuario no sabe un precio exacto, sugiere precios típicos mexicanos:
  - Corte de cabello: $100-200 (30-45 min)
  - Tinte: $400-800 (90-120 min)
  - Manicure: $150-250 (30-45 min)
  - Pedicure: $200-350 (45-60 min)
  - Barba: $80-150 (20-30 min)
  - Peinado: $200-400 (45-60 min)
- SIEMPRE muestra el menú actualizado después de agregar servicios
- El nombre del dueño que aparece arriba viene del perfil de WhatsApp y puede ser incorrecto. SIEMPRE pregunta al usuario por el nombre de su negocio — NUNCA uses el nombre del dueño como nombre del negocio ni como nombre de servicio.
- NO inventes información. Solo guarda lo que el usuario te diga
- Si el usuario quiere corregir algo, permítelo amablemente

## Restricciones
- NUNCA compartas información de otros negocios
- Si preguntan algo fuera del registro, redirige amablemente
- No hagas promesas sobre funcionalidades que no existen
- El servicio es GRATUITO durante el piloto - menciónalo si preguntan sobre costos
"""


class OnboardingHandler(ToolCallingMixin):
    """Handles business onboarding conversations.

    This creates Organizations immediately and tracks onboarding state
    directly in the Organization model.

    Uses Message table for conversation history (like ConversationHandler)
    to prevent race conditions when messages arrive quickly.
    """

    def __init__(
        self,
        db: AsyncSession,
        openai_client: OpenAIClient | None = None,
    ):
        """Initialize onboarding handler.

        Args:
            db: Database session
            openai_client: OpenAI client (uses singleton if not provided)
        """
        self.db = db
        self.client = openai_client or get_openai_client()

    async def get_or_create_organization(
        self,
        phone_number: str,
        sender_name: str | None = None,
    ) -> Organization:
        """Get existing onboarding org or create new one with ONBOARDING status.

        This creates:
        - Organization with status=ONBOARDING
        - Placeholder Location ("Principal")
        - Owner Staff with the sender's phone number

        Args:
            phone_number: User's phone number
            sender_name: Name from WhatsApp profile

        Returns:
            Organization (may be in ONBOARDING or ACTIVE status)
        """
        # Check for existing org by owner phone (via Staff)
        from app.services import staff as staff_service

        registrations = await staff_service.get_all_staff_registrations(self.db, phone_number)
        if registrations:
            # Return the first org (should be unique for onboarding flow)
            staff, org = registrations[0]
            logger.info(f"Found existing organization for {phone_number}: {org.id}")
            return org

        # Create new Organization with ONBOARDING status
        country_code = self._extract_country_code(phone_number)
        org = Organization(
            name=None,  # Set later during onboarding
            phone_country_code=country_code,
            phone_number=normalize_phone_number(phone_number),
            status=OrganizationStatus.ONBOARDING.value,
            onboarding_state=OnboardingState.INITIATED,
            onboarding_data={"owner_name": sender_name} if sender_name else {},
            onboarding_conversation_context={},
            last_message_at=datetime.now(UTC),
        )
        self.db.add(org)
        await self.db.flush()
        await self.db.refresh(org)
        logger.info(f"Created new organization {org.id} for onboarding")

        # Create placeholder Location
        location = Location(
            organization_id=org.id,
            name="Principal",
            is_primary=True,
        )
        self.db.add(location)
        await self.db.flush()
        await self.db.refresh(location)
        logger.info(f"Created placeholder location {location.id}")

        # Create owner Staff immediately (allows routing to work)
        owner_staff = Staff(
            organization_id=org.id,
            location_id=location.id,
            name=sender_name or "Dueño",
            phone_number=phone_number,
            role=StaffRole.OWNER.value,
            permission_level=ParloUserPermissionLevel.OWNER.value,
            is_active=True,
            permissions={"can_manage_all": True},
        )
        self.db.add(owner_staff)
        await self.db.flush()
        logger.info(f"Created owner staff {owner_staff.id}")

        return org

    @traced
    async def handle_message(
        self,
        org: Organization,
        message_content: str,
        message_id: str | None = None,
        media_url: str | None = None,
        content_type: str | None = None,
    ) -> str:
        """Handle an incoming message during onboarding.

        Uses Message table storage (like ConversationHandler) to prevent
        race conditions when messages arrive quickly. Each message is stored
        as an atomic INSERT, eliminating the lost-update problem with JSONB.

        Args:
            org: Organization being onboarded
            message_content: User's message
            message_id: WhatsApp message ID (for deduplication)

        Returns:
            AI response text
        """
        logger.info(f"Onboarding message for org {org.id}: {message_content[:50]}...")

        # Update last_message_at
        org.last_message_at = datetime.now(UTC)

        # Check if AI is configured
        if not self.client.is_configured:
            return self._get_fallback_response(org)

        # Get or create conversation for this onboarding (stored in Message table)
        conversation = await self._get_or_create_onboarding_conversation(org)

        # Store incoming message (atomic INSERT - no race condition)
        await self._store_message(
            conversation.id,
            MessageDirection.INBOUND,
            message_content,
            whatsapp_message_id=message_id,
            media_url=media_url,
            content_type=content_type,
        )

        # Get history from Message table (always current)
        history = await self._get_conversation_history(conversation.id)

        # Build system prompt
        system_prompt = build_onboarding_system_prompt(org)

        # Process with AI and tools using shared mixin
        async def execute_tool(tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
            return await self._execute_tool(org, tool_name, tool_input)

        response_text = await self._process_with_tools_generic(
            system_prompt=system_prompt,
            messages=history,
            tools=ONBOARDING_TOOLS,
            tool_executor=execute_tool,
            initial_tool_choice="auto",
        )

        # Store AI response (atomic INSERT)
        await self._store_message(
            conversation.id,
            MessageDirection.OUTBOUND,
            response_text,
        )

        await self.db.flush()

        return response_text

    async def _get_or_create_onboarding_conversation(self, org: Organization) -> Conversation:
        """Get or create Conversation for onboarding.

        Stores conversation_id in org.onboarding_data for persistence.

        Args:
            org: Organization being onboarded

        Returns:
            Conversation for this onboarding
        """
        # Check if we already have a conversation_id stored
        conv_id_str = (org.onboarding_data or {}).get("conversation_id")
        if conv_id_str:
            try:
                conv_id = UUID(conv_id_str)
                result = await self.db.execute(
                    select(Conversation).where(
                        Conversation.id == conv_id,
                        Conversation.organization_id == org.id,
                    )
                )
                conv = result.scalar_one_or_none()
                if conv:
                    return conv
            except (ValueError, TypeError):
                pass  # Invalid UUID, create new

        # Create new conversation (no end_customer for onboarding)
        conversation = Conversation(
            organization_id=org.id,
            end_customer_id=None,  # No customer for onboarding
            status=ConversationStatus.ACTIVE.value,
            context={"type": "onboarding"},
            last_message_at=datetime.now(UTC),
        )
        self.db.add(conversation)
        await self.db.flush()
        await self.db.refresh(conversation)

        # Store reference in onboarding_data
        org_data = dict(org.onboarding_data or {})
        org_data["conversation_id"] = str(conversation.id)
        org.onboarding_data = org_data

        logger.info(f"Created onboarding conversation {conversation.id} for org {org.id}")
        return conversation

    async def _get_conversation_history(self, conversation_id: UUID) -> list[dict[str, Any]]:
        """Get history from Message table (same pattern as ConversationHandler).

        Args:
            conversation_id: Conversation ID

        Returns:
            List of messages in OpenAI format
        """
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(20)
        )
        messages = list(reversed(result.scalars().all()))

        history = []
        for msg in messages:
            role = "user" if msg.direction == MessageDirection.INBOUND.value else "assistant"
            history.append(
                {
                    "role": role,
                    "content": msg.content,
                }
            )

        return history

    async def _store_message(
        self,
        conversation_id: UUID,
        direction: MessageDirection,
        content: str,
        whatsapp_message_id: str | None = None,
        media_url: str | None = None,
        content_type: str | None = None,
    ) -> Message:
        """Store message in Message table.

        Args:
            conversation_id: Conversation to store in
            direction: INBOUND or OUTBOUND
            content: Message content
            whatsapp_message_id: WhatsApp message ID (optional)
            media_url: URL of attached media (optional)
            content_type: Message content type (optional)

        Returns:
            Created Message
        """
        sender_type = (
            MessageSenderType.END_CUSTOMER.value
            if direction == MessageDirection.INBOUND
            else MessageSenderType.AI.value
        )

        message = Message(
            conversation_id=conversation_id,
            direction=direction.value,
            sender_type=sender_type,
            content_type=content_type or MessageContentType.TEXT.value,
            content=content,
            whatsapp_message_id=whatsapp_message_id,
            media_url=media_url,
        )
        self.db.add(message)
        await self.db.flush()
        return message

    @traced(trace_type="ai_tool")
    async def _execute_tool(
        self,
        org: Organization,
        tool_name: str,
        tool_input: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute an onboarding tool.

        Args:
            org: Organization being onboarded
            tool_name: Tool to execute
            tool_input: Tool parameters

        Returns:
            Tool result
        """
        import time

        start_time = time.time()

        logger.info(
            f"\n{'=' * 60}\n"
            f"🔧 ONBOARDING TOOL EXECUTION\n"
            f"{'=' * 60}\n"
            f"   Org ID: {org.id}\n"
            f"   State: {org.onboarding_state}\n"
            f"   Tool: {tool_name}\n"
            f"   Input: {tool_input}\n"
            f"{'=' * 60}"
        )

        collected = dict(org.onboarding_data or {})

        if tool_name == "save_business_info":
            collected["business_name"] = tool_input.get("business_name")
            collected["business_type"] = tool_input.get("business_type")
            collected["owner_name"] = tool_input.get("owner_name")
            if tool_input.get("address"):
                collected["address"] = tool_input.get("address")
            if tool_input.get("city"):
                collected["city"] = tool_input.get("city")
            org.onboarding_data = collected
            old_state = org.onboarding_state
            org.onboarding_state = OnboardingState.COLLECTING_SERVICES

            # Also update the org name and owner staff name
            org.name = collected["business_name"]

            # Update owner staff name if we got it
            if collected.get("owner_name"):
                result = await self.db.execute(
                    select(Staff).where(
                        Staff.organization_id == org.id,
                        Staff.role == StaffRole.OWNER.value,
                    )
                )
                owner = result.scalar_one_or_none()
                if owner:
                    owner.name = collected["owner_name"]

            await self.db.flush()
            elapsed_ms = (time.time() - start_time) * 1000
            logger.info(
                f"   ✅ save_business_info: {collected['business_name']} "
                f"(state: {old_state} → {org.onboarding_state}) ({elapsed_ms:.0f}ms)"
            )
            return {
                "success": True,
                "message": "Información del negocio guardada",
                "business_name": collected["business_name"],
                "owner_name": collected["owner_name"],
            }

        elif tool_name == "add_service":
            services = collected.get("services", [])
            new_service = {
                "name": tool_input.get("name"),
                "duration_minutes": tool_input.get("duration_minutes"),
                "price": tool_input.get("price"),
            }
            services.append(new_service)
            collected["services"] = services
            org.onboarding_data = collected
            await self.db.flush()

            # Return the full updated menu so AI can display it
            menu_items = []
            for svc in services:
                menu_items.append(
                    {
                        "name": svc["name"],
                        "price": f"${svc['price']:.0f}",
                        "duration": f"{svc['duration_minutes']} min",
                    }
                )

            elapsed_ms = (time.time() - start_time) * 1000
            logger.info(
                f"   ✅ add_service: {new_service['name']} "
                f"(${new_service['price']}, {new_service['duration_minutes']}min) "
                f"Total: {len(services)} services ({elapsed_ms:.0f}ms)"
            )
            return {
                "success": True,
                "message": f"Servicio '{new_service['name']}' agregado",
                "total_services": len(services),
                "current_menu": menu_items,
                "menu_display": _format_service_menu(services),
            }

        elif tool_name == "remove_service":
            services = collected.get("services", [])
            target_name = (tool_input.get("service_name") or "").strip().lower()
            original_count = len(services)
            services = [s for s in services if s["name"].strip().lower() != target_name]

            if len(services) == original_count:
                return {
                    "success": False,
                    "error": f"No se encontró el servicio '{tool_input.get('service_name')}'",
                    "current_menu": [
                        {
                            "name": s["name"],
                            "price": f"${s['price']:.0f}",
                            "duration": f"{s['duration_minutes']} min",
                        }
                        for s in services
                    ],
                    "menu_display": _format_service_menu(services),
                }

            collected["services"] = services
            org.onboarding_data = collected
            await self.db.flush()

            elapsed_ms = (time.time() - start_time) * 1000
            logger.info(
                f"   ✅ remove_service: removed '{tool_input.get('service_name')}' "
                f"({original_count} → {len(services)} services) ({elapsed_ms:.0f}ms)"
            )
            return {
                "success": True,
                "message": f"Servicio '{tool_input.get('service_name')}' eliminado",
                "total_services": len(services),
                "current_menu": [
                    {
                        "name": s["name"],
                        "price": f"${s['price']:.0f}",
                        "duration": f"{s['duration_minutes']} min",
                    }
                    for s in services
                ],
                "menu_display": _format_service_menu(services),
            }

        elif tool_name == "get_current_menu":
            services = collected.get("services", [])
            if not services:
                return {
                    "success": True,
                    "total_services": 0,
                    "current_menu": [],
                    "menu_display": "Sin servicios aún",
                }

            menu_items = []
            for svc in services:
                menu_items.append(
                    {
                        "name": svc["name"],
                        "price": f"${svc['price']:.0f}",
                        "duration": f"{svc['duration_minutes']} min",
                    }
                )

            return {
                "success": True,
                "total_services": len(services),
                "current_menu": menu_items,
                "menu_display": _format_service_menu(services),
            }

        elif tool_name == "add_staff_member":
            staff_list = collected.get("staff", [])
            phone = tool_input.get("phone_number", "")
            # Normalize phone number
            if phone and not phone.startswith("+"):
                if phone.startswith("52"):
                    phone = f"+{phone}"
                else:
                    phone = f"+52{phone}"

            new_staff = {
                "name": tool_input.get("name"),
                "phone_number": phone,
                "services": tool_input.get("services"),  # None means all services
            }
            staff_list.append(new_staff)
            collected["staff"] = staff_list
            org.onboarding_data = collected
            await self.db.flush()

            return {
                "success": True,
                "message": f"Empleado '{new_staff['name']}' agregado",
                "total_staff": len(staff_list) + 1,  # +1 for owner
                "staff_display": f"• {new_staff['name']} - {phone}",
            }

        elif tool_name == "save_business_hours":
            hours = {}
            for day in [
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
            ]:
                if day in tool_input:
                    hours[day] = tool_input[day]
            if hours:
                collected["business_hours"] = hours
                org.onboarding_data = collected
                await self.db.flush()
            return {"success": True, "message": "Horario guardado"}

        elif tool_name == "complete_onboarding":
            logger.info(
                f"   🎯 complete_onboarding called with confirmed={tool_input.get('confirmed')}"
            )

            if not tool_input.get("confirmed"):
                elapsed_ms = (time.time() - start_time) * 1000
                logger.warning(f"   ⚠️ complete_onboarding: User not confirmed ({elapsed_ms:.0f}ms)")
                return {"success": False, "message": "El usuario no confirmó"}

            # Verify we have minimum required data
            if not collected.get("business_name"):
                elapsed_ms = (time.time() - start_time) * 1000
                logger.warning(
                    f"   ⚠️ complete_onboarding: Missing business_name ({elapsed_ms:.0f}ms)"
                )
                return {"success": False, "error": "Falta el nombre del negocio"}
            if not collected.get("services"):
                elapsed_ms = (time.time() - start_time) * 1000
                logger.warning(f"   ⚠️ complete_onboarding: Missing services ({elapsed_ms:.0f}ms)")
                return {"success": False, "error": "Falta al menos un servicio"}

            # Auto-provision a WhatsApp number if not already done
            number_info = {}
            if collected.get("number_status") != "provisioned":
                logger.info(
                    f"   📞 Auto-provisioning WhatsApp number for {collected['business_name']}"
                )
                try:
                    result = await provision_number_for_business(
                        business_name=collected["business_name"],
                        webhook_base_url=_settings.app_base_url,
                        country_code="US",
                        db=self.db,
                        about_text=f"Agenda tu cita en {collected['business_name']} por WhatsApp",
                    )
                    if result:
                        collected["twilio_provisioned_number"] = result["phone_number"]
                        collected["twilio_phone_number_sid"] = result["phone_number_sid"]
                        collected["twilio_sender_sid"] = result.get("sender_sid")
                        collected["twilio_sender_status"] = result.get("sender_status")
                        collected["number_status"] = "provisioned"
                        org.onboarding_data = collected
                        await self.db.flush()
                        number_info = {
                            "phone_number": result["phone_number"],
                            "number_status": "provisioned",
                            "sender_status": result.get("sender_status"),
                        }
                        logger.info(f"   ✅ Provisioned number: {result['phone_number']}")
                    else:
                        collected["number_status"] = "pending"
                        org.onboarding_data = collected
                        await self.db.flush()
                        number_info = {"number_status": "pending"}
                        logger.warning(
                            "   ⚠️ Number provisioning failed, continuing with pending status"
                        )
                except Exception as e:
                    logger.error(f"   ⚠️ Number provisioning error: {e}", exc_info=True)
                    collected["number_status"] = "pending"
                    org.onboarding_data = collected
                    await self.db.flush()
                    number_info = {"number_status": "pending"}
            else:
                number_info = {
                    "phone_number": collected.get("twilio_provisioned_number"),
                    "number_status": "provisioned",
                    "sender_status": collected.get("twilio_sender_status"),
                }

            # Activate the organization
            try:
                logger.info(f"   📦 Activating organization: {collected.get('business_name')}")
                await self._activate_organization(org)
                elapsed_ms = (time.time() - start_time) * 1000
                logger.info(
                    f"\n{'🎉' * 20}\n"
                    f"   ONBOARDING COMPLETED!\n"
                    f"   Business: {org.name}\n"
                    f"   Org ID: {org.id}\n"
                    f"   Number: {number_info.get('phone_number', 'pending')}\n"
                    f"   Duration: {elapsed_ms:.0f}ms\n"
                    f"{'🎉' * 20}"
                )

                result = {
                    "success": True,
                    "message": "Registro completado",
                    "organization_id": str(org.id),
                    "business_name": org.name,
                }
                # Include number info so the AI can tell the user
                if number_info.get("phone_number"):
                    result["whatsapp_number"] = number_info["phone_number"]
                    result["number_message"] = (
                        f"Tu número de WhatsApp es {number_info['phone_number']}"
                    )
                else:
                    result["number_message"] = (
                        "Te asignaremos un número de WhatsApp pronto y te avisaremos por este chat"
                    )
                # Include website URL if configured
                if org.slug:
                    result["website_url"] = f"https://{org.slug}.parlo.mx"
                return result
            except Exception as e:
                elapsed_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"   ❌ Error activating organization: {e} ({elapsed_ms:.0f}ms)", exc_info=True
                )
                return {"success": False, "error": str(e)}

        elif tool_name == "send_dashboard_link":
            business_name = collected.get("business_name", "tu negocio")
            dashboard_url = f"{_settings.frontend_url}/login"

            website_line = ""
            if collected.get("wants_website") and collected.get("website_slug"):
                website_line = f"\n🌐 Tu página web: https://{collected['website_slug']}.parlo.mx\n"

            return {
                "success": True,
                "message": "Link del dashboard generado",
                "dashboard_url": dashboard_url,
                "business_name": business_name,
                "login_instructions": "Inicia sesión con tu número de WhatsApp, sin contraseña",
                "formatted_message": (
                    f"¡Felicidades! Tu cuenta de {business_name} está activa.\n\n"
                    f"📱 Dashboard: {dashboard_url}\n"
                    f"(Inicia sesión con tu número de WhatsApp, sin contraseña)"
                    f"{website_line}\n\n"
                    f"Tus clientes ya pueden escribirte por WhatsApp para agendar citas automáticamente."
                ),
            }

        elif tool_name == "provision_twilio_number":
            # Verify we have minimum required data before provisioning
            if not collected.get("business_name"):
                return {"success": False, "error": "Primero necesito el nombre del negocio"}
            if not collected.get("services"):
                return {"success": False, "error": "Primero necesito al menos un servicio"}

            business_name = collected["business_name"]
            country_code = tool_input.get("country_code", "US")

            try:
                # Provision a new Twilio WhatsApp number
                result = await provision_number_for_business(
                    business_name=business_name,
                    webhook_base_url=_settings.app_base_url,
                    country_code=country_code,
                    db=self.db,
                    about_text=f"Agenda tu cita en {business_name} por WhatsApp",
                )

                if result:
                    # SUCCESS: Store the provisioned number in onboarding data
                    collected["twilio_provisioned_number"] = result["phone_number"]
                    collected["twilio_phone_number_sid"] = result["phone_number_sid"]
                    collected["twilio_sender_sid"] = result.get("sender_sid")
                    collected["twilio_sender_status"] = result.get("sender_status")
                    collected["number_status"] = "provisioned"
                    org.onboarding_data = collected
                    await self.db.flush()

                    logger.info(
                        f"Provisioned Twilio number for {business_name}: "
                        f"{result['phone_number']} (sender_status={result.get('sender_status')})"
                    )

                    # Status-aware response
                    sender_status = result.get("sender_status")
                    if sender_status == "ONLINE":
                        return {
                            "success": True,
                            "message": "Número listo para WhatsApp",
                            "phone_number": result["phone_number"],
                            "formatted_message": (
                                f"¡Tu número {result['phone_number']} ya está activo para WhatsApp!"
                            ),
                        }
                    else:
                        return {
                            "success": True,
                            "message": "Número en proceso de activación",
                            "phone_number": result["phone_number"],
                            "sender_status": sender_status,
                            "formatted_message": (
                                f"¡Te asigné el número {result['phone_number']}!\n\n"
                                f"Está en proceso de activación para WhatsApp (toma unos minutos)."
                            ),
                        }
                else:
                    # FALLBACK: Queue for manual provisioning
                    collected["number_status"] = "pending"
                    org.onboarding_data = collected
                    await self.db.flush()

                    logger.warning(
                        f"Provisioning failed for {business_name}, queued for manual assignment"
                    )

                    return {
                        "success": True,  # Don't block onboarding
                        "number_status": "pending",
                        "formatted_message": (
                            "En este momento no tenemos números disponibles, pero no te preocupes.\n\n"
                            "Te asignaremos uno en las próximas horas y te avisaremos por WhatsApp."
                        ),
                    }

            except Exception as e:
                logger.error(f"Error provisioning Twilio number: {e}", exc_info=True)
                # FALLBACK on exception too
                collected["number_status"] = "pending"
                org.onboarding_data = collected
                await self.db.flush()

                return {
                    "success": True,  # Don't block onboarding
                    "number_status": "pending",
                    "formatted_message": (
                        "Hubo un problema al obtener tu número, pero no te preocupes.\n\n"
                        "Te asignaremos uno pronto y te avisaremos por WhatsApp."
                    ),
                }

        elif tool_name == "set_website_preference":
            wants_website = tool_input.get("wants_website", False)
            collected["wants_website"] = wants_website

            if wants_website:
                custom_slug = tool_input.get("custom_slug")
                if custom_slug:
                    # Validate and clean custom slug
                    from app.utils.slug import generate_slug, generate_unique_slug

                    clean = generate_slug(custom_slug)
                    if not clean:
                        return {
                            "success": False,
                            "error": "El slug no es válido, intenta con otro nombre",
                        }
                    slug = await generate_unique_slug(self.db, custom_slug)
                else:
                    # Generate from business name
                    from app.utils.slug import generate_unique_slug

                    business_name = collected.get("business_name", "negocio")
                    slug = await generate_unique_slug(self.db, business_name)

                collected["website_slug"] = slug
                org.onboarding_data = collected
                await self.db.flush()
                elapsed_ms = (time.time() - start_time) * 1000
                logger.info(f"   🌐 Website preference: {slug}.parlo.mx ({elapsed_ms:.0f}ms)")
                return {
                    "success": True,
                    "message": "Página web configurada",
                    "website_url": f"{slug}.parlo.mx",
                    "slug": slug,
                }
            else:
                org.onboarding_data = collected
                await self.db.flush()
                elapsed_ms = (time.time() - start_time) * 1000
                logger.info(f"   🌐 Website preference: no website ({elapsed_ms:.0f}ms)")
                return {"success": True, "message": "Sin página web"}

        result = {"error": f"Unknown tool: {tool_name}"}
        elapsed_ms = (time.time() - start_time) * 1000
        logger.warning(f"   ⚠️ Unknown tool: {tool_name} ({elapsed_ms:.0f}ms)")
        return result

    async def _create_availability_records(
        self,
        staff_id: UUID,
        business_hours: dict[str, Any],
    ) -> None:
        """Create RECURRING Availability records from business hours.

        Args:
            staff_id: Staff member to create availability for
            business_hours: Dict mapping day names to open/close times
        """
        for day_name, hours in business_hours.items():
            if hours.get("closed"):
                continue
            open_str = hours.get("open")
            close_str = hours.get("close")
            if not open_str or not close_str:
                continue
            day_of_week = DAY_NAME_TO_WEEKDAY.get(day_name)
            if day_of_week is None:
                continue
            open_parts = open_str.split(":")
            close_parts = close_str.split(":")
            start_time = dt_time(int(open_parts[0]), int(open_parts[1]))
            end_time = dt_time(int(close_parts[0]), int(close_parts[1]))
            availability = Availability(
                parlo_user_id=staff_id,
                type=AvailabilityType.RECURRING.value,
                day_of_week=day_of_week,
                start_time=start_time,
                end_time=end_time,
                is_available=True,
            )
            self.db.add(availability)

    @traced
    async def _activate_organization(self, org: Organization) -> None:
        """Activate an organization after onboarding completes.

        Creates ServiceTypes, Spots, and links everything together.
        Changes status from ONBOARDING to ACTIVE.

        Args:
            org: Organization to activate
        """
        collected = org.onboarding_data
        logger.info(f"Activating organization {org.id} from onboarding: {collected}")

        # Get the location (already created during get_or_create_organization)
        result = await self.db.execute(
            select(Location).where(
                Location.organization_id == org.id,
                Location.is_primary == True,
            )
        )
        location = result.scalar_one()

        # Update location with collected data
        address_parts = []
        if collected.get("address"):
            address_parts.append(collected["address"])
        if collected.get("city"):
            address_parts.append(collected["city"])
        location.address = ", ".join(address_parts) if address_parts else ""
        location.business_hours = collected.get("business_hours", DEFAULT_BUSINESS_HOURS)

        # Create Services
        services = []
        service_by_name = {}  # Map name to service for staff linking
        for svc_data in collected.get("services", []):
            # Convert price to cents (price_cents field stores cents)
            price_cents = int(svc_data["price"] * 100)
            service = ServiceType(
                organization_id=org.id,
                name=svc_data["name"],
                duration_minutes=svc_data["duration_minutes"],
                price_cents=price_cents,
                is_active=True,
            )
            self.db.add(service)
            services.append(service)
            service_by_name[svc_data["name"].lower()] = service

        await self.db.flush()
        for svc in services:
            await self.db.refresh(svc)
        logger.info(f"Created {len(services)} services")

        # Create default Spot
        spot = Spot(
            location_id=location.id,
            name="Estación 1",
            is_active=True,
        )
        # Assign service_types BEFORE flush to avoid lazy-load in async context
        spot.service_types = list(services)
        self.db.add(spot)
        await self.db.flush()
        await self.db.refresh(spot)
        logger.info(f"Created spot: {spot.id}")

        # Get owner staff and update with spot and services
        # Use selectinload to eagerly load service_types for async-safe access
        result = await self.db.execute(
            select(Staff)
            .options(selectinload(Staff.service_types))
            .where(
                Staff.organization_id == org.id,
                Staff.role == StaffRole.OWNER.value,
            )
        )
        owner_staff = result.scalar_one()
        owner_staff.default_spot_id = spot.id
        owner_staff.location_id = location.id

        # Link owner to all services
        owner_staff.service_types.extend(services)
        logger.info(f"Updated owner staff: {owner_staff.id}")

        # Create additional staff members collected during onboarding
        additional_staff = collected.get("staff", [])
        for staff_data in additional_staff:
            # Determine which services this staff member does
            staff_services = services  # Default: all services
            if staff_data.get("services"):
                # Filter to only specified services
                staff_services = []
                for svc_name in staff_data["services"]:
                    svc = service_by_name.get(svc_name.lower())
                    if svc:
                        staff_services.append(svc)
                # If no matches, assign all services
                if not staff_services:
                    staff_services = services

            employee = Staff(
                organization_id=org.id,
                location_id=location.id,
                default_spot_id=spot.id,
                name=staff_data["name"],
                phone_number=staff_data.get("phone_number", ""),
                role=StaffRole.EMPLOYEE.value,
                is_active=True,
                permissions={"can_view_schedule": True, "can_book": True},
            )
            # Assign service_types BEFORE flush to avoid lazy-load in async context
            employee.service_types = list(staff_services)
            self.db.add(employee)
            await self.db.flush()
            await self.db.refresh(employee)
            logger.info(f"Created staff (employee): {employee.id} - {employee.name}")

        # Create availability records for all staff from business hours
        business_hours = collected.get("business_hours", DEFAULT_BUSINESS_HOURS)
        all_staff_ids = [owner_staff.id] + [
            emp.id
            for emp in (
                await self.db.execute(
                    select(Staff).where(
                        Staff.organization_id == org.id,
                        Staff.role == StaffRole.EMPLOYEE.value,
                        Staff.is_active == True,
                    )
                )
            )
            .scalars()
            .all()
        ]
        for sid in all_staff_ids:
            await self._create_availability_records(sid, business_hours)
        await self.db.flush()
        logger.info(f"Created availability records for {len(all_staff_ids)} staff members")

        # Update organization settings and status
        org_settings = dict(org.settings or {})
        org_settings["language"] = "es"
        org_settings["currency"] = "MXN"
        org_settings["business_type"] = collected.get("business_type", "salon")

        number_status = collected.get("number_status", "pending")

        if collected.get("twilio_provisioned_number") and number_status == "provisioned":
            # Twilio provisioned number path
            provisioned_number = normalize_phone_number(collected["twilio_provisioned_number"])
            org.whatsapp_phone_number_id = provisioned_number
            org_settings["whatsapp_provider"] = "twilio"
            org_settings["twilio_phone_number"] = provisioned_number
            org_settings["twilio_phone_number_sid"] = collected.get("twilio_phone_number_sid")
            org_settings["sender_sid"] = collected.get("twilio_sender_sid")
            org_settings["sender_status"] = collected.get("twilio_sender_status")
            org_settings["number_status"] = "provisioned"
            # Mark as ready if sender is already ONLINE
            if collected.get("twilio_sender_status") == "ONLINE":
                org_settings["whatsapp_ready"] = True
                org_settings["number_status"] = "active"
            logger.info(
                f"Using Twilio provisioned number: {collected['twilio_provisioned_number']} "
                f"(sender_status={collected.get('twilio_sender_status')})"
            )
        elif number_status == "pending":
            # Fallback: no number assigned yet, queued for manual assignment
            # Don't set whatsapp_phone_number_id - they don't have one yet
            org_settings["whatsapp_provider"] = "pending"
            org_settings["number_status"] = "pending"
            logger.info(f"Org {org.id} activated with pending number assignment")
        else:
            # No WhatsApp setup at all - use owner phone as placeholder
            org.whatsapp_phone_number_id = org.phone_number
            org_settings["whatsapp_provider"] = "pending"
            org_settings["number_status"] = "pending"
            logger.info("No WhatsApp number provisioned, using owner phone as placeholder")

        org.settings = org_settings
        org.status = OrganizationStatus.ACTIVE.value
        org.onboarding_state = OnboardingState.COMPLETED

        # Set website slug if user opted in during onboarding
        if collected.get("wants_website") and collected.get("website_slug"):
            org.slug = collected["website_slug"]
            logger.info(f"Website slug set: {org.slug}.parlo.mx")

        await self.db.flush()
        logger.info(f"Organization {org.id} activated successfully")

    def _extract_country_code(self, phone: str) -> str:
        """Extract country code from phone number.

        Args:
            phone: Phone number like +521234567890

        Returns:
            Country code like "+52"
        """
        if phone.startswith("+"):
            phone = phone[1:]
        # Mexican numbers
        if phone.startswith("52"):
            return "+52"
        # US/Canada
        if phone.startswith("1"):
            return "+1"
        return "+52"  # Default to Mexico

    def _get_fallback_response(self, org: Organization) -> str:
        """Get fallback response when AI is not configured.

        Args:
            org: Organization being onboarded

        Returns:
            Fallback message
        """
        return (
            "¡Hola! Soy Parlo, tu asistente para agendar citas.\n\n"
            "Estamos preparando todo. "
            "Por favor intenta de nuevo en unos minutos."
        )


async def get_onboarding_organization_by_phone(
    db: AsyncSession,
    phone_number: str,
) -> Organization | None:
    """Get organization in ONBOARDING status for a phone number.

    Looks up by owner staff phone number.

    Args:
        db: Database session
        phone_number: Phone number to look up

    Returns:
        Organization in onboarding status or None
    """
    result = await db.execute(
        select(Organization)
        .join(Staff, Staff.organization_id == Organization.id)
        .where(
            Staff.phone_number == phone_number,
            Staff.role == StaffRole.OWNER.value,
            Organization.status == OrganizationStatus.ONBOARDING.value,
        )
    )
    return result.scalar_one_or_none()

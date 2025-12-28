# Yume: Project Initialization Prompt for Claude Code

## Instructions for Claude Code

You are initializing the codebase for **Yume**, a WhatsApp-native AI scheduling assistant for beauty businesses in Mexico. This document provides complete business and technical context. Your first task is to create the project structure, including a comprehensive README.md that will serve as the source of truth for any engineer or AI agent working on this codebase.

Read this entire document before writing any code. Ask clarifying questions if anything is ambiguous.

---

## Part 1: Business Context

### What is Yume?

Yume is a conversational AI that handles appointment scheduling for beauty businesses (barbershops, nail salons, hair salons, spas) in Mexico via WhatsApp. Business owners connect their existing WhatsApp number, and Yume automatically handles booking conversations with their customers.

**The one-liner:** "Connect Yume to your WhatsApp in 2 minutes. Watch your appointments start booking themselves."

### The Problem We Solve

Small beauty businesses in Mexico currently manage appointments through:
- Manual WhatsApp conversations (owner texts back and forth all day)
- Instagram DMs
- Phone calls
- Paper notebooks

This is painful because:
- Owners are constantly interrupted during haircuts/services to respond
- Messages get lost or forgotten, leading to missed bookings
- No systematic reminders, leading to no-shows
- No visibility into schedule until they check the notebook
- Can't easily see availability to quote to walk-ins

### Our Solution

Yume integrates with the business owner's existing WhatsApp number using Meta's Coexistence feature. When a customer messages to book:

1. Yume's AI handles the conversation naturally in Spanish
2. Checks real-time availability
3. Books the appointment
4. Sends confirmation to customer
5. Sends notification to business owner
6. Sends reminder before appointment

The business owner can watch all conversations happen in their WhatsApp Business App on their phone. They can take over any conversation manually if needed.

### Target Market (Wedge)

- **Geography:** Mexico (WhatsApp-dominant market, Coexistence supported)
- **Vertical:** Beauty services (barbershops, nail salons, hair salons, spas)
- **Size:** 1-10 employees (solo operators to small teams)
- **Initial cities:** Start with one metro area (likely CDMX, Guadalajara, or Monterrey)

### Business Model

**Freemium:**
- Free: First 50 bookings per month
- Paid: Unlimited bookings for $X MXN/month per location (price TBD, likely 299-499 MXN range)

**Future monetization** (not for v1, but architecture should accommodate):
- Marketing services (Google Business Profile setup, review requests, ads)
- Payments integration (deposits, prepayment)
- Multi-location management
- Staff/payroll features

### Key User Journeys

**Journey 1: Business Owner Onboarding (target: 10 minutes)**

```
Owner discovers Yume (ad, referral, social)
  → Clicks link to WhatsApp
  → Chats with Yume onboarding bot
  → Connects their WhatsApp via Embedded Signup (scans QR code)
  → Provides business name, services, prices, durations, hours
  → Done—ready to receive bookings
  → Optionally: access web dashboard for richer management
```

**Journey 2: Customer Booking (target: under 2 minutes)**

```
Customer messages business WhatsApp: "Hola, quiero una cita"
  → Yume responds, asks what service
  → Customer: "Un corte"
  → Yume shows available slots for requested timeframe
  → Customer picks slot
  → Yume confirms booking
  → Yume notifies business owner
  → Day before: Yume sends reminder to customer
  → After appointment: Yume optionally requests Google review
```

**Journey 3: Staff Daily Operations (via their personal WhatsApp)**

```
Staff member messages Yume from their registered phone number
  → Yume recognizes them as staff (not a customer)
  → Staff: "¿Qué tengo hoy?"
  → Yume shows their schedule for the day
  → Staff: "Bloquea de 2 a 3 para mi comida"
  → Yume blocks that time slot
  → Staff: "El cliente de las 11 no llegó"
  → Yume marks appointment as no-show
  → Staff can also book walk-ins, view customer history, etc.
```

**Journey 4: Business Owner Daily Operations**

```
Morning: Owner receives daily schedule summary via WhatsApp
During day: Gets notified of new bookings, can see in app
Anytime: Can message Yume "mi agenda" to see upcoming appointments
For complex tasks: Uses web dashboard (view week, manage staff, block time, etc.)
```

### Staff as WhatsApp Users

A key architectural decision: **staff members interact with Yume via their personal WhatsApp accounts.** This means:

1. During onboarding, the owner registers staff with their phone numbers
2. When a staff member messages the business's WhatsApp number, they're identified by their phone number and treated as staff (not customers)
3. Staff get a different set of capabilities than customers
4. No separate app needed—everyone uses WhatsApp

**How it works technically:**
- The business has ONE WhatsApp number (connected via Coexistence)
- Both customers AND staff message this same number
- When a message arrives, we look up the sender's phone number
- If it matches a registered staff member → staff conversation flow
- If not → customer conversation flow
- The owner also messages this number and gets owner-level capabilities

**Staff capabilities via WhatsApp:**
- View their own schedule ("¿Qué tengo hoy?", "¿Qué sigue?")
- View full business schedule (if permitted)
- Block off personal time ("Bloquea mañana de 2 a 4")
- Mark appointments as completed or no-show
- Book walk-in customers ("Acaba de llegar alguien para corte")
- View customer history ("¿Este cliente ha venido antes?")
- Cancel/reschedule on behalf of customers

**Owner-only capabilities:**
- Add/remove staff
- Change business hours
- Modify services and prices
- View business analytics
- Billing and account management

### Competitive Positioning

Competitors in scheduling:
- **Fresha, Booksy, Treatwell:** Marketplace-first, complex onboarding, designed for consumers not businesses
- **Calendly, Cal.com:** Not WhatsApp-native, not localized for Mexico, not vertical-specific
- **Square Appointments:** Payment-first, more complex than needed

Yume differentiators:
- WhatsApp-native (meets businesses where they are)
- AI-first (no app to learn, no buttons to click)
- Mexico-first (Spanish-native, local payment methods later, peso pricing)
- Radically simple onboarding (10 min via chat)
- Coexistence means owner watches it work in their own app

---

## Part 2: Technical Architecture

### Core Principles

1. **Data primitives over features:** The system is built around stable entities (Actors, Services, Appointments, etc.) that model service businesses generically. Features are orchestration on top of primitives.

2. **AI-native by construction:** Every API is typed and documented so AI agents can discover and use capabilities. The conversational AI is not a bolt-on; it's the primary interface.

3. **Extensibility for future verticals:** While we start with beauty/scheduling, the data model should support other service businesses (dental, auto repair, cleaning) and other features (payments, inventory) without rewriting core.

4. **Database as truth:** The database enforces invariants (referential integrity, time ordering, uniqueness). Business rules live in the application layer.

5. **Incremental identity:** Entities can be created with minimal data and enriched over time. A customer can exist with just a phone number; name comes later.

### Tech Stack

**Backend:**
- **Language:** Python 3.11+
- **Framework:** FastAPI
- **Validation:** Pydantic v2
- **Database:** PostgreSQL 15+
- **ORM:** SQLAlchemy 2.0 (async)
- **Migrations:** Alembic
- **Task Queue:** Redis + Celery (for reminders, async jobs)
- **AI/LLM:** Anthropic Claude API (for conversational AI)

**WhatsApp Integration:**
- **API:** Meta WhatsApp Cloud API (direct integration, no BSP)
- **Onboarding:** Embedded Signup with Coexistence flow
- **Webhooks:** Receive messages via Meta webhook

**Infrastructure (initial):**
- **Hosting:** Railway, Render, or Fly.io (simple PaaS to start)
- **Database:** Managed Postgres (Supabase, Railway, or Neon)
- **Redis:** Managed Redis (Upstash or Railway)
- **Secrets:** Environment variables (12-factor style)

**Frontend (later, not v1 priority):**
- **Framework:** Next.js 14+ (App Router)
- **Styling:** Tailwind CSS
- **Language:** TypeScript

### Data Model (Core Primitives)

```
┌─────────────────────────────────────────────────────────────────┐
│                         CORE ENTITIES                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Organization ─────────────── Location                          │
│       │                          │                              │
│       │                          │                              │
│       ▼                          ▼                              │
│    Staff ◄──────────────── Appointment ────────────► Customer   │
│       │                          │                              │
│       │                          │                              │
│       ▼                          ▼                              │
│  Availability              ServiceType                          │
│                                                                 │
│                                                                 │
│  Conversation ─────────────► Message                            │
│       │                                                         │
│       └──────────────────► Appointment (optional link)          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Entity Definitions:**

```python
# Organization: The business entity (e.g., "Barbería Don Carlos")
Organization:
    id: UUID
    name: str
    phone_country_code: str  # +52 for Mexico
    phone_number: str        # The WhatsApp-connected number
    whatsapp_phone_number_id: str  # Meta's phone number ID
    whatsapp_waba_id: str    # WhatsApp Business Account ID
    timezone: str            # e.g., "America/Mexico_City"
    status: enum (onboarding, active, suspended, churned)
    settings: JSONB          # Flexible config
    created_at: datetime
    updated_at: datetime

# Location: Physical location (supports multi-location later)
Location:
    id: UUID
    organization_id: FK → Organization
    name: str
    address: str (optional)
    is_primary: bool
    business_hours: JSONB    # {mon: {open: "10:00", close: "20:00"}, ...}
    created_at: datetime
    updated_at: datetime

# Staff: People who provide services (also users who can interact via WhatsApp)
Staff:
    id: UUID
    organization_id: FK → Organization
    location_id: FK → Location (optional, null = all locations)
    name: str
    phone_number: str             # Their personal WhatsApp - used to identify them as staff
    role: enum (owner, employee)
    permissions: JSONB            # {can_view_schedule: true, can_book: true, can_cancel: true, ...}
    is_active: bool
    settings: JSONB
    created_at: datetime
    updated_at: datetime
    
    # Unique constraint: (organization_id, phone_number)
    # This phone number is how we identify staff when they message Yume

# ServiceType: What the business offers
ServiceType:
    id: UUID
    organization_id: FK → Organization
    name: str                # "Corte de cabello"
    description: str (optional)
    duration_minutes: int    # 45
    price_cents: int         # 15000 = $150.00 MXN
    currency: str            # "MXN"
    is_active: bool
    settings: JSONB          # e.g., {requires_deposit: false}
    created_at: datetime
    updated_at: datetime

# Customer: End consumers who book appointments
Customer:
    id: UUID
    organization_id: FK → Organization
    phone_number: str        # Primary identifier, may be only data initially
    name: str (optional)     # Learned over time
    email: str (optional)
    notes: str (optional)    # Business owner's notes
    settings: JSONB
    created_at: datetime
    updated_at: datetime
    
    # Unique constraint: (organization_id, phone_number)

# Appointment: A scheduled service event
Appointment:
    id: UUID
    organization_id: FK → Organization
    location_id: FK → Location
    customer_id: FK → Customer
    staff_id: FK → Staff (optional, null = any available)
    service_type_id: FK → ServiceType
    
    scheduled_start: datetime (with timezone)
    scheduled_end: datetime (with timezone)
    
    status: enum (pending, confirmed, completed, cancelled, no_show)
    source: enum (whatsapp, web, manual, walk_in)
    
    notes: str (optional)
    cancellation_reason: str (optional)
    
    reminder_sent_at: datetime (optional)
    
    created_at: datetime
    updated_at: datetime
    
    # Constraint: scheduled_start < scheduled_end
    # Constraint: no overlapping appointments for same staff

# Conversation: A WhatsApp conversation thread
Conversation:
    id: UUID
    organization_id: FK → Organization
    customer_id: FK → Customer
    whatsapp_conversation_id: str (optional, Meta's ID)
    
    status: enum (active, resolved, handed_off)
    context: JSONB           # AI conversation state
    
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime

# Message: Individual messages in a conversation
Message:
    id: UUID
    conversation_id: FK → Conversation
    
    direction: enum (inbound, outbound)
    sender_type: enum (customer, ai, staff)
    
    content_type: enum (text, image, audio, template)
    content: text            # Message body
    media_url: str (optional)
    
    whatsapp_message_id: str (optional)
    
    created_at: datetime
    
    # Appointments can be linked to the message that created them
    # via a separate AppointmentMessage join table if needed

# Availability: Staff availability patterns and exceptions
Availability:
    id: UUID
    staff_id: FK → Staff
    
    type: enum (recurring, exception)
    
    # For recurring: day of week pattern
    day_of_week: int (optional, 0=Monday)
    start_time: time
    end_time: time
    
    # For exceptions: specific date range
    exception_date: date (optional)
    is_available: bool       # false = blocked off
    
    created_at: datetime
    updated_at: datetime
```

### API Design

RESTful API with OpenAPI documentation auto-generated by FastAPI.

**Endpoint Structure:**

```
# Organization management (used during onboarding and by dashboard)
POST   /api/v1/organizations              # Create org (onboarding start)
GET    /api/v1/organizations/{id}         # Get org details
PATCH  /api/v1/organizations/{id}         # Update org
POST   /api/v1/organizations/{id}/connect-whatsapp  # Complete Embedded Signup

# Services
GET    /api/v1/organizations/{org_id}/services
POST   /api/v1/organizations/{org_id}/services
PATCH  /api/v1/organizations/{org_id}/services/{id}
DELETE /api/v1/organizations/{org_id}/services/{id}

# Staff
GET    /api/v1/organizations/{org_id}/staff
POST   /api/v1/organizations/{org_id}/staff
PATCH  /api/v1/organizations/{org_id}/staff/{id}

# Customers
GET    /api/v1/organizations/{org_id}/customers
GET    /api/v1/organizations/{org_id}/customers/{id}
POST   /api/v1/organizations/{org_id}/customers
PATCH  /api/v1/organizations/{org_id}/customers/{id}

# Appointments
GET    /api/v1/organizations/{org_id}/appointments
POST   /api/v1/organizations/{org_id}/appointments
GET    /api/v1/organizations/{org_id}/appointments/{id}
PATCH  /api/v1/organizations/{org_id}/appointments/{id}
POST   /api/v1/organizations/{org_id}/appointments/{id}/cancel
POST   /api/v1/organizations/{org_id}/appointments/{id}/complete

# Availability
GET    /api/v1/organizations/{org_id}/availability
GET    /api/v1/organizations/{org_id}/availability/slots  # Available slots for booking
POST   /api/v1/organizations/{org_id}/availability
DELETE /api/v1/organizations/{org_id}/availability/{id}

# WhatsApp Webhook (Meta calls this)
POST   /api/v1/webhooks/whatsapp
GET    /api/v1/webhooks/whatsapp  # Webhook verification

# Conversations (mostly internal, used by AI and dashboard)
GET    /api/v1/organizations/{org_id}/conversations
GET    /api/v1/organizations/{org_id}/conversations/{id}
GET    /api/v1/organizations/{org_id}/conversations/{id}/messages
```

### WhatsApp Integration Details

**Meta Cloud API Direct Integration:**

1. **Embedded Signup with Coexistence:**
   - We host the Embedded Signup flow (Meta's JavaScript SDK)
   - Business owner logs into Facebook, selects their WhatsApp Business App number
   - They scan a QR code in their WhatsApp Business App
   - We receive access token and phone number ID
   - Their existing number now works with our API AND their app simultaneously

2. **Webhook Setup:**
   - Register webhook URL with Meta: `https://api.yume.mx/api/v1/webhooks/whatsapp`
   - Subscribe to: `messages`, `message_status`, `message_template_status`
   - Verify webhook with challenge/response

3. **Receiving Messages:**
   ```python
   # Webhook payload structure (simplified)
   {
       "object": "whatsapp_business_account",
       "entry": [{
           "id": "WABA_ID",
           "changes": [{
               "field": "messages",
               "value": {
                   "messaging_product": "whatsapp",
                   "metadata": {
                       "phone_number_id": "PHONE_NUMBER_ID"
                   },
                   "contacts": [{"wa_id": "521234567890", "profile": {"name": "Juan"}}],
                   "messages": [{
                       "from": "521234567890",
                       "id": "MESSAGE_ID",
                       "timestamp": "1234567890",
                       "type": "text",
                       "text": {"body": "Hola, quiero una cita"}
                   }]
               }
           }]
       }]
   }
   ```

4. **Sending Messages:**
   ```python
   # Send text message
   POST https://graph.facebook.com/v18.0/{phone_number_id}/messages
   {
       "messaging_product": "whatsapp",
       "to": "521234567890",
       "type": "text",
       "text": {"body": "¡Hola! Claro, ¿qué servicio te gustaría?"}
   }
   
   # Send template message (for notifications outside 24h window)
   POST https://graph.facebook.com/v18.0/{phone_number_id}/messages
   {
       "messaging_product": "whatsapp",
       "to": "521234567890",
       "type": "template",
       "template": {
           "name": "appointment_reminder",
           "language": {"code": "es_MX"},
           "components": [{
               "type": "body",
               "parameters": [
                   {"type": "text", "text": "mañana a las 3:00 PM"},
                   {"type": "text", "text": "Corte de cabello"}
               ]
           }]
       }
   }
   ```

5. **Template Messages Needed (submit to Meta for approval):**
   - `appointment_confirmation` - Sent when appointment is booked
   - `appointment_reminder` - Sent 24h before appointment
   - `appointment_cancelled` - Sent when appointment is cancelled
   - `review_request` - Sent after appointment (optional, for growth)

### Conversational AI Architecture

**LLM Integration:**

```python
# Core conversation handler
class ConversationHandler:
    def __init__(self, anthropic_client, organization, customer, conversation):
        self.client = anthropic_client
        self.org = organization
        self.customer = customer
        self.conversation = conversation
    
    async def process_message(self, message_text: str) -> str:
        # Build context for Claude
        system_prompt = self.build_system_prompt()
        conversation_history = await self.get_conversation_history()
        
        # Call Claude with tools
        response = await self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system_prompt,
            messages=conversation_history + [{"role": "user", "content": message_text}],
            tools=self.get_available_tools()
        )
        
        # Handle tool calls (check availability, book appointment, etc.)
        # Return final response text
```

**Available Tools for AI:**

```python
tools = [
    {
        "name": "check_availability",
        "description": "Check available appointment slots for a given date range and service",
        "input_schema": {
            "type": "object",
            "properties": {
                "service_id": {"type": "string"},
                "date_from": {"type": "string", "format": "date"},
                "date_to": {"type": "string", "format": "date"},
                "preferred_staff_id": {"type": "string", "optional": True}
            },
            "required": ["service_id", "date_from"]
        }
    },
    {
        "name": "book_appointment",
        "description": "Book an appointment for the customer",
        "input_schema": {
            "type": "object",
            "properties": {
                "service_id": {"type": "string"},
                "staff_id": {"type": "string"},
                "start_time": {"type": "string", "format": "datetime"},
                "customer_name": {"type": "string", "optional": True}
            },
            "required": ["service_id", "start_time"]
        }
    },
    {
        "name": "get_customer_appointments",
        "description": "Get upcoming appointments for the current customer",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "cancel_appointment",
        "description": "Cancel an existing appointment",
        "input_schema": {
            "type": "object",
            "properties": {
                "appointment_id": {"type": "string"},
                "reason": {"type": "string", "optional": True}
            },
            "required": ["appointment_id"]
        }
    },
    {
        "name": "reschedule_appointment",
        "description": "Reschedule an existing appointment to a new time",
        "input_schema": {
            "type": "object",
            "properties": {
                "appointment_id": {"type": "string"},
                "new_start_time": {"type": "string", "format": "datetime"}
            },
            "required": ["appointment_id", "new_start_time"]
        }
    },
    {
        "name": "handoff_to_human",
        "description": "Transfer the conversation to the business owner when AI cannot help or customer requests it",
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {"type": "string"}
            },
            "required": ["reason"]
        }
    }
]

# Additional tools available ONLY for staff/owner conversations
staff_tools = [
    {
        "name": "get_my_schedule",
        "description": "Get the staff member's own schedule for a given date range",
        "input_schema": {
            "type": "object",
            "properties": {
                "date_from": {"type": "string", "format": "date"},
                "date_to": {"type": "string", "format": "date"}
            }
        }
    },
    {
        "name": "get_business_schedule",
        "description": "Get the full business schedule (all staff) for a given date range",
        "input_schema": {
            "type": "object",
            "properties": {
                "date_from": {"type": "string", "format": "date"},
                "date_to": {"type": "string", "format": "date"}
            }
        }
    },
    {
        "name": "block_time",
        "description": "Block off time in the staff member's schedule (for lunch, personal time, etc.)",
        "input_schema": {
            "type": "object",
            "properties": {
                "start_time": {"type": "string", "format": "datetime"},
                "end_time": {"type": "string", "format": "datetime"},
                "reason": {"type": "string", "optional": True}
            },
            "required": ["start_time", "end_time"]
        }
    },
    {
        "name": "mark_appointment_status",
        "description": "Mark an appointment as completed, no-show, or cancelled",
        "input_schema": {
            "type": "object",
            "properties": {
                "appointment_id": {"type": "string"},
                "status": {"type": "string", "enum": ["completed", "no_show", "cancelled"]},
                "notes": {"type": "string", "optional": True}
            },
            "required": ["appointment_id", "status"]
        }
    },
    {
        "name": "book_walk_in",
        "description": "Book a walk-in customer who just arrived",
        "input_schema": {
            "type": "object",
            "properties": {
                "service_id": {"type": "string"},
                "customer_phone": {"type": "string", "optional": True},
                "customer_name": {"type": "string", "optional": True},
                "staff_id": {"type": "string", "optional": True}
            },
            "required": ["service_id"]
        }
    },
    {
        "name": "get_customer_history",
        "description": "Look up a customer's appointment history",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_phone": {"type": "string"}
            },
            "required": ["customer_phone"]
        }
    },
    {
        "name": "send_message_to_customer",
        "description": "Send a WhatsApp message to a customer on behalf of the business",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_phone": {"type": "string"},
                "message": {"type": "string"}
            },
            "required": ["customer_phone", "message"]
        }
    }
]
```

**System Prompt Structure:**

```python
def build_system_prompt(self) -> str:
    # Different prompts for staff vs customers
    if self.is_staff_conversation:
        return self.build_staff_system_prompt()
    else:
        return self.build_customer_system_prompt()
```

**Message Routing Logic:**

When a message arrives via webhook, we need to determine if it's from a customer or staff:

```python
async def route_incoming_message(phone_number_id: str, sender_phone: str, message: str):
    # 1. Find the organization by the WhatsApp phone number ID
    org = await get_org_by_whatsapp_phone_id(phone_number_id)
    
    # 2. Check if sender is a registered staff member
    staff = await get_staff_by_phone(org.id, sender_phone)
    
    if staff:
        # This is a staff member - use staff conversation handler
        return await handle_staff_message(org, staff, message)
    else:
        # This is a customer - use customer conversation handler
        customer = await get_or_create_customer(org.id, sender_phone)
        return await handle_customer_message(org, customer, message)
```

**Customer System Prompt:**

```python
def build_system_prompt(self) -> str:
    return f"""Eres Yume, la asistente virtual de {self.org.name}. Tu trabajo es ayudar a los clientes a agendar citas de manera amable y eficiente.

## Información del Negocio
- Nombre: {self.org.name}
- Servicios disponibles:
{self.format_services()}
- Horario de atención:
{self.format_business_hours()}

## Información del Cliente
- Teléfono: {self.customer.phone_number}
- Nombre: {self.customer.name or "No proporcionado aún"}
- Citas anteriores: {self.format_previous_appointments()}

## Instrucciones
1. Sé amable, profesional y concisa. Usa español mexicano natural.
2. Si el cliente quiere agendar, pregunta qué servicio desea y para cuándo.
3. Usa la herramienta check_availability para ver horarios disponibles antes de ofrecer opciones.
4. Confirma siempre los detalles antes de agendar: servicio, fecha, hora.
5. Si el cliente pregunta algo que no puedes resolver (precios especiales, quejas, preguntas complejas), usa handoff_to_human.
6. Si no conoces el nombre del cliente y es natural preguntar, hazlo.
7. Después de agendar, confirma todos los detalles y despídete amablemente.

## Restricciones
- Nunca inventes horarios disponibles. Siempre usa check_availability.
- No hagas más de una pregunta a la vez.
- Si hay ambigüedad (ej: "mañana" sin hora), pregunta para clarificar.
- Responde solo en español.
"""

def build_staff_system_prompt(self) -> str:
    return f"""Eres Yume, la asistente virtual de {self.org.name}. Estás hablando con {self.staff.name}, que es {self.staff.role} del negocio.

## Información del Negocio
- Nombre: {self.org.name}
- Servicios disponibles:
{self.format_services()}
- Horario de atención:
{self.format_business_hours()}

## Información del Empleado
- Nombre: {self.staff.name}
- Rol: {self.staff.role}
- Permisos: {self.format_permissions()}

## Capacidades
Como empleado, {self.staff.name} puede pedirte:
1. Ver su agenda del día o de fechas específicas
2. Ver la agenda completa del negocio (si tiene permiso)
3. Bloquear tiempo personal (comida, descanso, citas personales)
4. Marcar citas como completadas o no-show
5. Registrar clientes que llegan sin cita (walk-ins)
6. Consultar historial de clientes
7. Enviar mensajes a clientes en nombre del negocio

## Instrucciones
1. Sé concisa y eficiente. Los empleados quieren respuestas rápidas.
2. Si preguntan por "mi agenda", muestra SU agenda personal, no la del negocio.
3. Confirma acciones importantes antes de ejecutarlas (cancelaciones, cambios).
4. Si piden algo fuera de sus permisos, explícalo amablemente.
5. Para acciones que afectan clientes (cancelar citas), ofrece notificar al cliente.

## Formato de respuestas
- Para agendas, usa formato de lista clara con hora, servicio y cliente
- Para confirmaciones, sé breve: "Listo, bloqueado de 2 a 3 PM ✓"
- Usa emojis con moderación para claridad (✓, ⏰, 👤)
"""
```

### Project Structure

```
yume/
├── README.md                    # Comprehensive project documentation
├── pyproject.toml               # Python dependencies (using Poetry or uv)
├── alembic.ini                  # Database migrations config
├── .env.example                 # Environment variables template
├── docker-compose.yml           # Local development setup
│
├── alembic/
│   └── versions/                # Migration files
│
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entry point
│   ├── config.py                # Settings management (pydantic-settings)
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py              # Dependency injection (db sessions, auth, etc.)
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py        # Main API router
│   │       ├── organizations.py
│   │       ├── services.py
│   │       ├── appointments.py
│   │       ├── customers.py
│   │       ├── availability.py
│   │       ├── staff.py
│   │       └── webhooks.py      # WhatsApp webhook handlers
│   │
│   ├── models/                  # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── base.py              # Base model class
│   │   ├── organization.py
│   │   ├── location.py
│   │   ├── staff.py
│   │   ├── service_type.py
│   │   ├── customer.py
│   │   ├── appointment.py
│   │   ├── conversation.py
│   │   ├── message.py
│   │   └── availability.py
│   │
│   ├── schemas/                 # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── organization.py
│   │   ├── appointment.py
│   │   ├── customer.py
│   │   └── ... (matching models)
│   │
│   ├── services/                # Business logic layer
│   │   ├── __init__.py
│   │   ├── scheduling.py        # Availability and booking logic
│   │   ├── whatsapp.py          # WhatsApp API client
│   │   ├── conversation.py      # AI conversation handler
│   │   └── notifications.py     # Reminders and alerts
│   │
│   ├── ai/                      # AI/LLM related code
│   │   ├── __init__.py
│   │   ├── client.py            # Anthropic client wrapper
│   │   ├── prompts.py           # System prompts and templates
│   │   └── tools.py             # Tool definitions for Claude
│   │
│   ├── tasks/                   # Celery background tasks
│   │   ├── __init__.py
│   │   ├── reminders.py         # Send appointment reminders
│   │   └── analytics.py         # Usage tracking, etc.
│   │
│   └── utils/
│       ├── __init__.py
│       ├── datetime.py          # Timezone handling
│       └── phone.py             # Phone number parsing/formatting
│
├── tests/
│   ├── conftest.py
│   ├── test_api/
│   ├── test_services/
│   └── test_ai/
│
└── scripts/
    ├── seed_dev_data.py         # Development data seeding
    └── create_whatsapp_templates.py  # Submit templates to Meta
```

### Environment Variables

```bash
# .env.example

# Application
APP_ENV=development  # development, staging, production
APP_SECRET_KEY=your-secret-key-here
APP_BASE_URL=https://api.yume.mx

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/yume

# Redis
REDIS_URL=redis://localhost:6379/0

# Meta WhatsApp
META_APP_ID=your-meta-app-id
META_APP_SECRET=your-meta-app-secret
META_WEBHOOK_VERIFY_TOKEN=your-webhook-verify-token
META_API_VERSION=v18.0

# Anthropic
ANTHROPIC_API_KEY=your-anthropic-api-key

# Observability (optional for v1)
SENTRY_DSN=
```

### Development Setup Instructions

```bash
# 1. Clone and enter project
git clone <repo>
cd yume

# 2. Install dependencies (using uv for speed)
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# 3. Start infrastructure
docker-compose up -d  # Postgres + Redis

# 4. Run migrations
alembic upgrade head

# 5. Seed development data (optional)
python scripts/seed_dev_data.py

# 6. Start the server
uvicorn app.main:app --reload

# 7. In another terminal, start Celery worker
celery -A app.tasks worker --loglevel=info

# 8. For WhatsApp webhook testing locally, use ngrok
ngrok http 8000
# Update Meta webhook URL to ngrok URL
```

---

## Part 3: Implementation Priorities

### Phase 1: Core Backend (Week 1-2)

1. **Project setup:** Poetry/uv, FastAPI scaffold, Docker Compose
2. **Database models and migrations:** All core entities including Staff with phone numbers
3. **Basic CRUD APIs:** Organizations, Services, Customers, Staff, Appointments
4. **Availability engine:** Calculate available slots given business hours and existing appointments
5. **Staff identification logic:** Lookup by phone number to distinguish staff from customers

**Deliverable:** API that can create organizations, services, staff, and appointments via REST. Tests passing.

### Phase 2: WhatsApp Integration (Week 3-4)

1. **Meta Cloud API client:** Send messages, receive webhooks
2. **Webhook handler:** Parse incoming messages, route to conversation handler
3. **Embedded Signup flow:** Simple web page to initiate Coexistence connection
4. **Message templates:** Create and submit to Meta for approval

**Deliverable:** Can receive WhatsApp messages via webhook and send responses. Embedded Signup works.

### Phase 3: Conversational AI (Week 5-6)

1. **Anthropic client wrapper:** Handle API calls with retry logic
2. **Message routing:** Identify staff vs customer by phone number lookup
3. **Customer conversation handler:** Booking flow with customer tools
4. **Staff conversation handler:** Schedule management with staff tools
5. **Tool implementations:** All tools for both customer and staff flows
6. **System prompt refinement:** Iterate on Spanish natural language quality for both personas

**Deliverable:** Full booking conversation works for customers, full schedule management works for staff, both end-to-end via WhatsApp.

### Phase 4: Notifications & Polish (Week 7-8)

1. **Celery tasks:** Appointment reminders, daily schedule summary
2. **Onboarding flow completion:** Full 10-minute chat-based setup
3. **Error handling:** Graceful failures, human handoff
4. **Basic monitoring:** Logging, error tracking

**Deliverable:** Production-ready MVP for pilot users.

---

## Part 4: What to Build First

Start with this order:

1. **Create project structure** as specified above
2. **Write README.md** with business context and technical overview (this is critical for any future engineer or AI agent)
3. **Set up database models** (start with Organization, ServiceType, Customer, Appointment)
4. **Implement availability calculation** (this is the core scheduling logic)
5. **Create basic REST APIs** for appointments
6. **Add WhatsApp webhook endpoint** (even before full integration, have the endpoint ready)

Do NOT start with:
- Frontend (we don't need it for MVP)
- Complex analytics
- Multi-location support (v2)
- Payments (future)

---

## Part 5: Key Decisions Already Made

These are settled—don't revisit:

1. **WhatsApp Cloud API direct, not via Twilio** — Cost savings, same functionality
2. **Coexistence feature** — Business keeps their existing number
3. **Spanish (Mexican) only for v1** — Don't internationalize yet
4. **Single location per org for v1** — Multi-location is v2
5. **PostgreSQL** — The right choice for relational data with JSONB flexibility
6. **FastAPI + Pydantic** — Type safety and auto-docs
7. **Claude for AI** — Best for nuanced Spanish conversation
8. **Staff interact via same WhatsApp number** — One number for everything, staff identified by phone number lookup
9. **No separate staff app for v1** — Staff use WhatsApp, dashboard can come later

---

## Part 6: Open Questions (Decide as you build)

1. **Hosting choice:** Railway vs Render vs Fly.io — pick based on ease of setup
2. **Celery vs alternatives:** Could use APScheduler or ARQ if simpler
3. **Testing strategy:** Pytest, but decide on fixtures and mocking approach
4. **Logging/monitoring:** Structlog? Logfire? Basic logging to start is fine.

---

## Appendix: Example Conversations

### Example 1: Simple Booking

```
Cliente: Hola buenas tardes
Yume: ¡Hola! Bienvenido a Barbería Don Carlos. ¿En qué puedo ayudarte?

Cliente: Quiero una cita para un corte
Yume: ¡Claro! ¿Para qué día te gustaría agendar tu corte?

Cliente: Mañana en la tarde
Yume: Perfecto. Mañana viernes tengo disponibles estos horarios para corte de cabello ($150):
• 3:00 PM
• 4:00 PM  
• 5:30 PM
¿Cuál te funciona mejor?

Cliente: A las 4
Yume: Listo, te agendé tu corte de cabello para mañana viernes a las 4:00 PM. 
¿Me confirmas tu nombre para la cita?

Cliente: Juan Pérez
Yume: ¡Perfecto, Juan! Tu cita está confirmada:
📅 Viernes 15 de enero
⏰ 4:00 PM
💇 Corte de cabello - $150

Te enviaré un recordatorio mañana. ¡Nos vemos!

Cliente: Gracias
Yume: ¡Con gusto! Que tengas buena tarde. 👋
```

### Example 2: Rescheduling

```
Cliente: Hola, necesito cambiar mi cita de mañana
Yume: Hola Juan, claro que sí. Veo que tienes una cita para corte mañana viernes a las 4:00 PM. ¿Para cuándo te gustaría cambiarla?

Cliente: Para el sábado si hay espacio
Yume: El sábado tengo estos horarios disponibles:
• 10:00 AM
• 11:30 AM
• 2:00 PM
¿Cuál prefieres?

Cliente: 11:30
Yume: Listo, cambié tu cita para el sábado a las 11:30 AM. ¿Todo bien?

Cliente: Sí perfecto gracias
Yume: ¡Excelente! Nos vemos el sábado, Juan. 👍
```

### Example 3: Handoff

```
Cliente: Oye quiero saber si hacen tintes para hombre
Yume: Actualmente los servicios que tenemos son corte de cabello y arreglo de barba. Para preguntas sobre servicios adicionales, deja que le pase tu mensaje a Carlos, el dueño.

[Notificación a Carlos: "Un cliente pregunta por tintes para hombre. Teléfono: +52 55 1234 5678"]

Yume: Ya le avisé a Carlos, te contactará pronto para darte más información. ¿Hay algo más en lo que pueda ayudarte?
```

### Example 4: Staff Checking Schedule

```
[Message from registered staff phone number]

Pedro (empleado): Qué tengo hoy?
Yume: Hola Pedro, aquí está tu agenda para hoy viernes:

⏰ 10:00 AM - Corte - Juan Pérez
⏰ 11:00 AM - Corte y barba - Miguel Sánchez  
⏰ 12:30 PM - Corte - Luis Ramírez
🍽️ 2:00 PM - 3:00 PM - Bloqueado (comida)
⏰ 3:00 PM - Barba - Carlos Mendoza
⏰ 4:00 PM - Disponible
⏰ 5:00 PM - Corte - Roberto García

Tienes 5 citas y un espacio libre a las 4.

Pedro: Bloquea las 4, tengo que salir temprano
Yume: Listo, bloqueé las 4:00 PM ✓ ¿Quieres que también bloquee de 5 en adelante?

Pedro: No solo las 4
Yume: Perfecto, solo las 4:00 PM bloqueadas. ¿Algo más?
```

### Example 5: Staff Handling Walk-in

```
María (empleada): Acaba de llegar alguien para uñas
Yume: ¿Qué servicio quiere? Tenemos:
• Manicure - $200 (45 min)
• Pedicure - $250 (1 hr)
• Mani + Pedi - $400 (1.5 hr)

María: Mani pedi
Yume: Perfecto. ¿Tienes el teléfono de la clienta para registrarla?

María: 55 9876 5432
Yume: Registrado. ¿Nombre?

María: Ana
Yume: Listo ✓ Registré a Ana (55 9876 5432) para Mani + Pedi ahora a las 11:30 AM contigo.

María: 👍
```

### Example 6: Staff Marking No-Show

```
Carlos (dueño): El de las 3 no llegó
Yume: ¿Te refieres a la cita de Roberto García a las 3:00 PM (Corte)?

Carlos: Si
Yume: Marqué la cita como no-show ✓ ¿Quieres que le envíe un mensaje a Roberto?

Carlos: Si, dile que esperamos que esté bien y que nos avise para reagendar
Yume: Enviado ✓ Le mandé: "Hola Roberto, notamos que no pudiste llegar a tu cita de hoy. Esperamos que todo esté bien. Cuando gustes, escríbenos para reagendar. - Barbería Don Carlos"
```

### Example 7: Owner Adding Staff

```
Carlos (dueño): Quiero agregar un nuevo empleado
Yume: ¡Claro! Necesito algunos datos:
1. ¿Cómo se llama?

Carlos: Pedro Hernández
Yume: 2. ¿Cuál es su número de WhatsApp?

Carlos: 55 1111 2222
Yume: 3. ¿Qué servicios va a ofrecer Pedro?
• Corte de cabello
• Arreglo de barba
• Corte y barba

Carlos: Todos
Yume: Perfecto. Agregué a Pedro Hernández (55 1111 2222) como empleado ✓

Ahora Pedro puede escribirme desde su WhatsApp para:
- Ver su agenda
- Bloquear tiempo
- Marcar citas completadas
- Registrar walk-ins

¿Quieres que le mande un mensaje de bienvenida explicándole cómo usar Yume?

Carlos: Si
Yume: Enviado ✓
```

---

## Final Note

This is a real product that will serve real small business owners. Quality matters. The AI needs to feel natural and helpful, not robotic. The booking flow needs to be rock solid—a missed appointment damages trust.

Build with care. Ship incrementally. Test with real messages in Spanish.

¡Éxito! 🚀

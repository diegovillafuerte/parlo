# Yume - WhatsApp-Native AI Scheduling Assistant

**"Connect Yume to your WhatsApp in 2 minutes. Watch your appointments start booking themselves."**

Yume is a conversational AI that handles appointment scheduling for beauty businesses (barbershops, nail salons, hair salons, spas) in Mexico via WhatsApp. Business owners connect their existing WhatsApp number, and Yume automatically handles booking conversations with their customers.

## Table of Contents

- [What is Yume?](#what-is-yume)
- [The Problem We Solve](#the-problem-we-solve)
- [Our Solution](#our-solution)
- [Target Market](#target-market)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Development](#development)
- [Database](#database)
- [Architecture](#architecture)
- [Core Entities](#core-entities)
- [Contributing](#contributing)

## What is Yume?

Yume integrates with a business owner's existing WhatsApp number using Meta's Coexistence feature. When a customer messages to book:

1. Yume's AI handles the conversation naturally in Mexican Spanish
2. Checks real-time availability
3. Books the appointment
4. Sends confirmation to customer
5. Sends notification to business owner
6. Sends reminder before appointment

The business owner can watch all conversations happen in their WhatsApp Business App on their phone. They can take over any conversation manually if needed.

## The Problem We Solve

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

## Our Solution

### For Customers
A natural, conversational booking experience via WhatsApp:
```
Cliente: Hola, quiero una cita para un corte
Yume: ¡Claro! ¿Para qué día te gustaría agendar tu corte?
Cliente: Mañana en la tarde
Yume: Perfecto. Mañana viernes tengo disponibles estos horarios...
```

### For Business Owners
- **2-minute setup**: Connect WhatsApp via Embedded Signup
- **Automated booking**: AI handles all customer conversations
- **Same WhatsApp number**: Keep your existing number with Coexistence
- **Full visibility**: See all conversations in your WhatsApp app
- **Manual takeover**: Jump into any conversation when needed

### For Staff Members
Staff interact with Yume via their personal WhatsApp accounts:
```
Pedro (empleado): Qué tengo hoy?
Yume: Hola Pedro, aquí está tu agenda para hoy viernes:
⏰ 10:00 AM - Corte - Juan Pérez
⏰ 11:00 AM - Corte y barba - Miguel Sánchez
...
```

**Key architectural decision**: Staff are identified by their phone numbers. When a registered staff member messages the business's WhatsApp number, they get staff capabilities instead of customer booking flow.

## Target Market

- **Geography**: Mexico (WhatsApp-dominant market, Coexistence supported)
- **Vertical**: Beauty services (barbershops, nail salons, hair salons, spas)
- **Size**: 1-10 employees (solo operators to small teams)
- **Initial cities**: Start with one metro area (CDMX, Guadalajara, or Monterrey)

## Key Features

### v1 Features
- ✅ WhatsApp-native booking conversations (customers)
- ✅ WhatsApp-native schedule management (staff)
- ✅ Staff identification by phone number
- ✅ Real-time availability checking
- ✅ Appointment booking, rescheduling, cancellation
- ✅ Automated reminders
- ✅ Walk-in customer registration
- ✅ Customer history lookup
- ✅ Mexican Spanish only

### What We're NOT Building (v1)
- ❌ Frontend dashboard (WhatsApp is the UI)
- ❌ Multi-location support
- ❌ Payments/deposits
- ❌ English or other languages
- ❌ Complex analytics
- ❌ Email notifications
- ❌ Mobile app

## Tech Stack

**Backend**
- Python 3.11+
- FastAPI (async web framework)
- Pydantic v2 (validation)
- PostgreSQL 15+ (database)
- SQLAlchemy 2.0 (async ORM)
- Alembic (migrations)
- Redis + Celery (background tasks)

**Integrations**
- Anthropic Claude API (conversational AI)
- Meta WhatsApp Cloud API (direct, no BSP)

**Infrastructure (initial)**
- Docker Compose (local development)
- Railway/Render/Fly.io (hosting)
- Managed Postgres and Redis

## Project Structure

```
yume/
├── README.md                    # This file
├── CLAUDE.md                    # Quick reference for development
├── docs/
│   └── PROJECT_SPEC.md          # Full project specification
├── pyproject.toml               # Python dependencies
├── alembic.ini                  # Database migrations config
├── .env.example                 # Environment variables template
├── docker-compose.yml           # Local development setup
│
├── alembic/
│   └── versions/                # Migration files
│
├── app/
│   ├── main.py                  # FastAPI application entry point
│   ├── config.py                # Settings management (pydantic-settings)
│   ├── database.py              # Database connection
│   │
│   ├── api/
│   │   ├── deps.py              # Dependency injection
│   │   └── v1/
│   │       ├── router.py        # Main API router
│   │       └── ...              # API endpoints (organizations, appointments, etc.)
│   │
│   ├── models/                  # SQLAlchemy models
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
│   ├── schemas/                 # Pydantic schemas (request/response)
│   ├── services/                # Business logic layer
│   ├── ai/                      # LLM integration
│   └── tasks/                   # Celery background tasks
│
├── tests/
│   ├── test_api/
│   ├── test_services/
│   └── test_ai/
│
└── scripts/
    └── seed_dev_data.py         # Development data seeding
```

## Quick Start

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Installation

1. **Clone the repository**
   ```bash
   git clone <repo>
   cd yume
   ```

2. **Create virtual environment and install dependencies**
   ```bash
   # Using uv (recommended for speed)
   uv venv
   source .venv/bin/activate
   uv pip install -e ".[dev]"

   # Or using pip
   python -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   ```

3. **Start infrastructure**
   ```bash
   docker-compose up -d  # Start Postgres + Redis
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start the server**
   ```bash
   uvicorn app.main:app --reload
   ```

7. **Verify it's running**
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status":"ok"}
   ```

The API is now running at `http://localhost:8000`.
- API docs: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

## Development

### Common Commands

```bash
# Development setup
docker-compose up -d              # Start Postgres + Redis
source .venv/bin/activate         # Activate virtualenv
alembic upgrade head              # Run migrations
uvicorn app.main:app --reload     # Start API server

# Testing
pytest                            # Run all tests
pytest tests/test_api/            # Run API tests only
pytest -x                         # Stop on first failure

# Database
alembic revision --autogenerate -m "description"  # Create migration
alembic upgrade head              # Apply migrations
alembic downgrade -1              # Rollback one migration

# Background tasks
celery -A app.tasks worker --loglevel=info

# Local webhook testing
ngrok http 8000                   # Expose local server for Meta webhooks
```

### Code Quality

```bash
# Linting and formatting
ruff check .                      # Check for linting errors
ruff check --fix .                # Fix auto-fixable errors
ruff format .                     # Format code

# Type checking
mypy app/                         # Run type checker
```

## Database

### Core Entities

The system is built around stable data primitives:

| Entity | Purpose |
|--------|---------|
| **Organization** | The business (barbershop, salon) |
| **Location** | Physical location (single for v1) |
| **Staff** | Employees + owner, **identified by phone number** |
| **ServiceType** | What they offer (haircut, manicure) |
| **Customer** | End consumers, minimal data initially |
| **Appointment** | Scheduled service events |
| **Conversation** | WhatsApp conversation thread |
| **Message** | Individual messages |
| **Availability** | Staff schedules and exceptions |

### Entity Relationships

```
Organization ─────────────── Location
     │                          │
     │                          │
     ▼                          ▼
  Staff ◄──────────────── Appointment ────────────► Customer
     │                          │
     │                          │
     ▼                          ▼
Availability              ServiceType


Conversation ─────────────► Message
     │
     └──────────────────► Appointment (optional link)
```

### Critical Pattern: Staff Identification

**Staff members are identified by their phone numbers:**
- During onboarding, the owner registers staff with their phone numbers
- When a message arrives, we look up the sender's phone number
- If it matches a registered staff member → staff conversation flow
- If not → customer conversation flow
- This enables staff to use their personal WhatsApp to interact with Yume

## Architecture

### Message Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   WhatsApp      │────▶│   FastAPI       │────▶│   PostgreSQL    │
│   Cloud API     │◀────│   Backend       │◀────│                 │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                        ┌────────┴────────┐
                        ▼                 ▼
               ┌─────────────┐   ┌─────────────────┐
               │   Claude    │   │   Redis/Celery  │
               │   (AI)      │   │   (Tasks)       │
               └─────────────┘   └─────────────────┘
```

### Conversation Routing

```python
async def route_incoming_message(phone_number_id: str, sender_phone: str, message: str):
    # 1. Find the organization
    org = await get_org_by_whatsapp_phone_id(phone_number_id)

    # 2. Check if sender is a registered staff member
    staff = await get_staff_by_phone(org.id, sender_phone)

    if staff:
        # Staff member - use staff conversation handler
        return await handle_staff_message(org, staff, message)
    else:
        # Customer - use customer conversation handler
        customer = await get_or_create_customer(org.id, sender_phone)
        return await handle_customer_message(org, customer, message)
```

## Core Principles

1. **Data primitives over features**: The system is built around stable entities (Actors, Services, Appointments, etc.) that model service businesses generically.

2. **AI-native by construction**: Every API is typed and documented so AI agents can discover and use capabilities. The conversational AI is not a bolt-on; it's the primary interface.

3. **Incremental identity**: Entities can be created with minimal data and enriched over time. A customer can exist with just a phone number; name comes later.

4. **Database as truth**: The database enforces invariants. Business rules live in the application layer.

5. **WhatsApp is the UI**: Everything happens via chat. No web dashboard required for v1.

6. **Spanish only**: Mexican Spanish, natural tone. Use "tú" not "usted". Currency in MXN. Timezone: America/Mexico_City.

## Language & Localization

- **All AI responses in Mexican Spanish** - natural, not formal
- Use "tú" not "usted"
- Currency in MXN (Mexican pesos)
- Timezone default: America/Mexico_City
- Date format: "viernes 15 de enero" not "15/01"
- Time format: "3:00 PM" (12-hour with AM/PM)

## Environment Variables

Required variables (see `.env.example`):

```bash
# Application
APP_ENV=development
APP_SECRET_KEY=your-secret-key
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
```

## Contributing

### Key Files to Understand

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI application entry point |
| `app/models/` | SQLAlchemy database models |
| `app/config.py` | Application settings |
| `app/database.py` | Database connection management |
| `CLAUDE.md` | Quick reference for development |
| `docs/PROJECT_SPEC.md` | Full project specification |

### Development Guidelines

1. **All times in UTC**: Store everything in UTC. Convert to org timezone only for display.
2. **Async all the way**: Use async/await for all database and external API calls.
3. **Type everything**: Use type hints everywhere. Pydantic for validation.
4. **Test with real Spanish**: AI quality only shows in real conversations.

### Adding a New Feature

1. Define Pydantic schemas in `app/schemas/`
2. Add route in `app/api/v1/`
3. Add business logic in `app/services/`
4. Add tests in `tests/`

### Database Migrations

1. Modify model in `app/models/`
2. Generate migration: `alembic revision --autogenerate -m "description"`
3. Review the generated migration file
4. Apply: `alembic upgrade head`

## External Documentation

- [Meta WhatsApp Cloud API](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [Embedded Signup](https://developers.facebook.com/docs/whatsapp/embedded-signup)
- [Anthropic Claude API](https://docs.anthropic.com/claude/reference)
- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)

## License

[Add license information]

---

**Built with ❤️ for small business owners in Mexico**

For comprehensive technical details, see `CLAUDE.md` and `docs/PROJECT_SPEC.md`.

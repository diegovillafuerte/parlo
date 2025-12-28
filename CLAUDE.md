# CLAUDE.md - Yume Project Guide

## What is Yume?

Yume is a WhatsApp-native AI scheduling assistant for beauty businesses in Mexico. Business owners connect their existing WhatsApp number, and Yume handles booking conversations with customers automatically. Staff members can also interact with Yume via WhatsApp to manage their schedules.

**One-liner:** "Connect Yume to your WhatsApp in 2 minutes. Watch your appointments start booking themselves."

## Quick Reference

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

## Architecture Overview

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

**Key flow:** WhatsApp webhook → Identify sender (staff or customer) → Route to appropriate AI handler → AI uses tools to check availability/book/etc → Send response via WhatsApp API

## Tech Stack

- **Python 3.11+** with **FastAPI** and **Pydantic v2**
- **PostgreSQL 15+** with **SQLAlchemy 2.0** (async)
- **Redis + Celery** for background tasks
- **Anthropic Claude** for conversational AI
- **Meta WhatsApp Cloud API** (direct, no BSP)

## Project Structure

```
yume/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Settings (pydantic-settings)
│   ├── api/v1/              # API endpoints
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   ├── ai/                  # LLM integration
│   └── tasks/               # Celery tasks
├── alembic/                 # Database migrations
├── tests/
└── scripts/
```

## Core Entities

| Entity | Purpose |
|--------|---------|
| Organization | The business (barbershop, salon) |
| Location | Physical location (single for v1) |
| Staff | Employees + owner, identified by phone number |
| ServiceType | What they offer (haircut, manicure) |
| Customer | End consumers, minimal data initially |
| Appointment | Scheduled service events |
| Conversation | WhatsApp conversation thread |
| Message | Individual messages |
| Availability | Staff schedules and exceptions |

## Critical Patterns

### 1. Message Routing

Every incoming WhatsApp message must be routed correctly:

```python
async def route_message(sender_phone: str, org: Organization):
    staff = await get_staff_by_phone(org.id, sender_phone)
    if staff:
        return StaffConversationHandler(org, staff)
    else:
        customer = await get_or_create_customer(org.id, sender_phone)
        return CustomerConversationHandler(org, customer)
```

### 2. Incremental Identity

Customers can exist with minimal data. Don't require fields upfront:

```python
# Good - create with just phone
customer = Customer(organization_id=org.id, phone_number=phone)

# Name comes later during conversation
customer.name = name_from_conversation
```

### 3. All Times in UTC

Store everything in UTC. Convert to org timezone only for display:

```python
from datetime import datetime, timezone

# Storage
appointment.scheduled_start = datetime.now(timezone.utc)

# Display
local_time = appointment.scheduled_start.astimezone(org_timezone)
```

### 4. Tool-Based AI

The AI doesn't access the database directly. It uses typed tools:

```python
# AI decides to book → calls tool → we execute
tools = [
    "check_availability",
    "book_appointment", 
    "cancel_appointment",
    # ... etc
]
```

### 5. Webhook Idempotency

WhatsApp may send duplicate webhooks. Handle gracefully:

```python
# Store message IDs, skip if already processed
if await message_exists(whatsapp_message_id):
    return {"status": "already_processed"}
```

## API Conventions

- All endpoints under `/api/v1/`
- Organization-scoped: `/api/v1/organizations/{org_id}/resource`
- Use Pydantic schemas for all request/response bodies
- Return 404 for missing resources, 422 for validation errors
- Async all the way down

## Language & Localization

- **All AI responses in Mexican Spanish** - natural, not formal
- Use "tú" not "usted" 
- Currency in MXN (Mexican pesos)
- Timezone default: America/Mexico_City
- Date format: "viernes 15 de enero" not "15/01"
- Time format: "3:00 PM" (12-hour with AM/PM)

## What NOT to Build (v1)

- ❌ Frontend/dashboard (WhatsApp is the UI)
- ❌ Multi-location support
- ❌ Payments/deposits
- ❌ English or other languages
- ❌ Complex analytics
- ❌ Email notifications
- ❌ Mobile app

## Environment Variables

Required in `.env`:

```bash
DATABASE_URL=postgresql+asyncpg://...
REDIS_URL=redis://...
ANTHROPIC_API_KEY=sk-ant-...
META_APP_ID=...
META_APP_SECRET=...
META_WEBHOOK_VERIFY_TOKEN=...
```

## Testing Guidelines

- Use pytest with async support (`pytest-asyncio`)
- Factory fixtures for creating test data
- Mock external APIs (WhatsApp, Claude) in tests
- Test both staff and customer conversation flows
- Test availability calculation edge cases thoroughly

```python
# Example test structure
async def test_booking_flow(db_session, mock_claude, mock_whatsapp):
    org = await create_test_org(db_session)
    customer_phone = "+525512345678"
    
    # Simulate incoming message
    response = await handle_message(org, customer_phone, "Quiero una cita")
    
    assert "qué servicio" in response.lower()
```

## Common Tasks

### Adding a new API endpoint

1. Add Pydantic schemas in `app/schemas/`
2. Add route in `app/api/v1/`
3. Add business logic in `app/services/`
4. Add tests in `tests/test_api/`

### Adding a new AI tool

1. Define tool schema in `app/ai/tools.py`
2. Implement handler in `app/services/`
3. Add to appropriate tool list (customer_tools or staff_tools)
4. Test with real conversation flow

### Adding a database migration

1. Modify model in `app/models/`
2. Run `alembic revision --autogenerate -m "description"`
3. Review generated migration
4. Run `alembic upgrade head`

## Debugging Tips

- Check webhook logs for incoming message format
- Use `print(response.model_dump_json(indent=2))` for Claude responses
- WhatsApp webhook must respond within 20 seconds
- If AI seems stuck, check tool call/response format

## Key Files to Understand

| File | Purpose |
|------|---------|
| `app/api/v1/webhooks.py` | WhatsApp webhook handler |
| `app/services/conversation.py` | AI conversation orchestration |
| `app/services/scheduling.py` | Availability calculation |
| `app/ai/tools.py` | Tool definitions for Claude |
| `app/ai/prompts.py` | System prompts (customer & staff) |

## External Documentation

- [Meta WhatsApp Cloud API](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [Embedded Signup](https://developers.facebook.com/docs/whatsapp/embedded-signup)
- [Anthropic Claude API](https://docs.anthropic.com/claude/reference)
- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)

## Getting Help

For comprehensive business context, user journeys, data models, and example conversations, see:
- `docs/PROJECT_SPEC.md` - Full project specification
- `MEMORY.md` - Project progress tracker (update after each task)

## Session Workflow

**Starting a session:**
1. Read `MEMORY.md` to see current status and what's done
2. Read `CLAUDE.md` for conventions
3. Reference `docs/PROJECT_SPEC.md` as needed for deep context

**Ending a task:**
1. Confirm code works (tests pass, server runs)
2. Update `MEMORY.md`:
   - Add completed task with date and details
   - Check off items in checklists
   - Update "Current Status" section
   - Add any notes for next session

## Remember

1. **WhatsApp is the UI** - Everything happens via chat
2. **Staff are users too** - Same number, different experience based on phone lookup
3. **Spanish only** - Mexican Spanish, natural tone
4. **Simple first** - Don't over-engineer, ship incrementally
5. **Test with real messages** - AI quality only shows in real conversations

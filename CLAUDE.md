# CLAUDE.md - Yume Development Guide

## What is Yume?

Yume is a WhatsApp-native AI scheduling assistant for beauty businesses in Mexico. Business owners connect their WhatsApp number, and Yume handles booking conversations automatically via AI.

**One-liner:** "Connect Yume to your WhatsApp in 2 minutes. Watch your appointments start booking themselves."

**Full specification:** See `docs/PROJECT_SPEC.md` for detailed requirements, user journeys, and example conversations.

## Quick Reference

```bash
# Start infrastructure
docker-compose up -d              # Postgres + Redis

# Backend
source .venv/bin/activate
alembic upgrade head              # Run migrations
uvicorn app.main:app --reload     # Start API (port 8000)

# Frontend
cd frontend && npm run dev        # Start Next.js (port 3000)
cd frontend && npm run build      # Build for production

# Testing
pytest                            # Run all tests
pytest -x                         # Stop on first failure

# Database
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1

# Local webhook testing
ngrok http 8000                   # For Twilio webhooks
```

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   WhatsApp      │────▶│   FastAPI       │────▶│   PostgreSQL    │
│   (Twilio)      │◀────│   Backend       │◀────│                 │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                        ┌────────┼────────┐
                        ▼        ▼        ▼
               ┌─────────────┐ ┌───────┐ ┌─────────────┐
               │   OpenAI    │ │ Redis │ │   Next.js   │
               │   GPT-4.1   │ │       │ │   Frontend  │
               └─────────────┘ └───────┘ └─────────────┘
```

**Three interfaces:**
1. **WhatsApp** - Customers book, staff manage schedules (via Twilio)
2. **Web Dashboard** - Business owners manage everything (magic link auth)
3. **Admin Dashboard** - Platform management (password auth)

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11+, FastAPI, Pydantic v2 |
| Database | PostgreSQL 15+, SQLAlchemy 2.0 (async), Alembic |
| AI | OpenAI GPT-4.1 with function calling |
| WhatsApp | Twilio WhatsApp API |
| Frontend | Next.js 15, TypeScript, Tailwind CSS |
| Background | Redis + Celery (not yet implemented) |

## Project Structure

```
yume/
├── app/                         # Backend
│   ├── main.py                  # FastAPI entry
│   ├── config.py                # Settings
│   ├── api/v1/                  # Endpoints (~57 routes)
│   ├── models/                  # SQLAlchemy (14 models)
│   ├── schemas/                 # Pydantic schemas
│   ├── services/                # Business logic
│   ├── ai/                      # OpenAI integration
│   └── tasks/                   # Celery tasks (empty)
├── frontend/                    # Next.js app
│   └── src/
│       ├── app/                 # Pages (13 routes)
│       ├── components/          # UI components
│       ├── lib/api/             # API client
│       └── providers/           # Auth, Location context
├── alembic/                     # Migrations
└── docs/PROJECT_SPEC.md         # Requirements (source of truth)
```

## Core Entities

| Entity | Purpose |
|--------|---------|
| Organization | The business |
| Location | Physical location (1+ per org) |
| Spot | Service station (chair, table) - linked to services |
| Staff | Employees identified by phone |
| ServiceType | What they offer |
| Customer | End consumer (incremental identity) |
| Appointment | Scheduled event |
| Conversation/Message | WhatsApp threads |
| Availability | Staff schedules |
| AuthToken | Magic link tokens |

**Key relationships:**
- Staff ↔ ServiceType: many-to-many (what staff can do)
- Spot ↔ ServiceType: many-to-many (what spot supports)
- Appointment requires: customer, service, spot, (optional) staff

## Critical Patterns

### 1. Message Routing (THE CORE)
```python
# Incoming WhatsApp → identify sender → route to correct handler
staff = await get_staff_by_phone(org.id, sender_phone)
if staff:
    return handle_staff_message(org, staff, message)
else:
    customer = await get_or_create_customer(org.id, sender_phone)
    return handle_customer_message(org, customer, message)
```

### 2. Dual Authentication
- **Business owners:** Magic link via WhatsApp → JWT (7 days)
- **Admin:** Password → JWT (shorter expiry)
- Frontend uses different tokens: `auth_token` vs `admin_token`

### 3. Tool-Based AI
AI uses typed tools, never accesses DB directly:
- Customer tools: check_availability, book_appointment, cancel, reschedule
- Staff tools: get_schedule, block_time, mark_complete, book_walk_in

### 4. All Times in UTC
Store UTC, convert to org timezone only for display.

### 5. Webhook Idempotency
Check message_id before processing to handle duplicate deliveries.

## Environment Variables

Backend `.env`:
```bash
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/yume
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=sk-...
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
JWT_SECRET_KEY=change-in-production
FRONTEND_URL=http://localhost:3000
ADMIN_MASTER_PASSWORD=change-in-production
```

Frontend `.env.local`:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## Current Implementation Status

### Fully Implemented
- All 14 database models with proper relationships
- ~57 API endpoints for all resources
- Admin dashboard (stats, org management, impersonation, conversations, activity)
- AI conversation handler with tool calling (customer + staff flows)
- Message routing (staff vs customer identification)
- Availability slot calculation
- Magic link authentication
- Frontend: login, location management, company settings

### Partially Implemented
- Schedule page (UI done, data not fully wired)
- Appointment creation (missing conflict validation)
- WhatsApp sending (Twilio client exists, template messages need setup)

### Not Implemented
- Background tasks (Celery) - `app/tasks/` is empty
- Appointment reminders
- Daily schedule summaries
- WhatsApp onboarding flow (owner setup via chat)
- Embedded Signup (Meta) - currently using Twilio

## Key Files

| File | What it does |
|------|--------------|
| `app/api/v1/webhooks.py` | Twilio webhook handler |
| `app/services/message_router.py` | Staff/customer routing |
| `app/services/conversation.py` | AI orchestration |
| `app/services/scheduling.py` | Availability calculation |
| `app/ai/tools.py` | AI tool definitions |
| `app/ai/prompts.py` | System prompts (Spanish) |
| `frontend/src/providers/AuthProvider.tsx` | Auth context |
| `frontend/src/lib/api/client.ts` | Axios with dual token handling |

## Development Guidelines

### Spanish Only
- All AI responses in Mexican Spanish
- Use "tú" not "usted"
- Currency: MXN, prices as "$150"
- Dates: "viernes 15 de enero"
- Times: "3:00 PM" (12-hour)

### Organization Scoping
Every query must filter by `organization_id` to prevent data leakage.

### Avoid Over-Engineering
- No abstractions for one-time operations
- Simple solutions over complex patterns
- Don't add features beyond what's requested

### Testing
- Use pytest with async support
- Mock external APIs (Twilio, OpenAI)
- Test availability edge cases thoroughly

## Debugging

- Webhook logs show incoming message format
- WhatsApp webhook must respond within 20 seconds
- Check tool call format if AI seems stuck
- Admin dashboard has conversation viewer for debugging

## Session Workflow

**Starting:**
1. Read `workplan.md` for current status
2. Reference this file for conventions
3. See `docs/PROJECT_SPEC.md` for requirements

**Ending:**
1. Verify backend loads, frontend builds
2. Update `workplan.md` with completed tasks

## References

- **Requirements:** `docs/PROJECT_SPEC.md` (source of truth)
- **Progress:** `workplan.md`
- [Twilio WhatsApp](https://www.twilio.com/docs/whatsapp)
- [OpenAI API](https://platform.openai.com/docs/api-reference)
- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)

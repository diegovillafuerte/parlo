# CLAUDE.md - Parlo Development Guide

## Core Principle
You can test everything yourself. Use simulation, evals, and Playwright.
Never report "done" without verifying. See `docs/testing.md` for details.

## What is Parlo?
WhatsApp-native AI scheduling assistant for beauty businesses in Mexico.
See `docs/PROJECT_SPEC.md` for full specification.

## Quick Reference

```bash
# Start infrastructure
docker-compose up -d              # Postgres + Redis + Celery

# Backend
source .venv/bin/activate
alembic upgrade head              # Run migrations
uvicorn app.main:app --reload     # Start API (port 8000)

# Frontend
cd frontend && npm run dev        # Start Next.js (port 3000)
cd frontend && npm run build      # Build for production

# Celery (for background tasks like reminders)
celery -A app.tasks.celery_app worker --loglevel=info  # Worker
celery -A app.tasks.celery_app beat --loglevel=info    # Scheduler

# Testing
pytest                            # Run all tests
pytest -x                         # Stop on first failure
pytest tests/evals/ --run-evals -v  # Run AI evals (needs real OPENAI_API_KEY)

# Simulation (local dev — requires server running)
# POST /api/v1/simulate/message with admin auth
# GET  /api/v1/simulate/recipients with admin auth

# Database
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1

# Linting
ruff check .                      # Lint Python
ruff format --check .             # Check Python formatting
cd frontend && npm run lint       # Lint TypeScript
python scripts/lint_golden_rules.py  # Check golden rules
python scripts/validate_docs.py   # Validate doc structure
```

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         WHATSAPP CHANNELS (Twilio)                        │
├────────────────────────────────┬─────────────────────────────────────────┤
│   PARLO CENTRAL NUMBER          │      BUSINESS NUMBERS (per business)    │
│   - Business onboarding        │      - End customer bookings            │
│   - Business management        │      - Staff management                 │
└────────────────────────────────┴─────────────────────────────────────────┘
                                    │
                                    ▼
              ┌─────────────────────────────────────────┐
              │           FastAPI Backend               │
              │   (Message Router → State Machines)     │
              └──────────────────┬──────────────────────┘
                                 │
            ┌────────────────────┼────────────────────┐
            ▼                    ▼                    ▼
   ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
   │  PostgreSQL │      │   OpenAI    │      │   Next.js   │
   │             │      │   gpt-4.1   │      │   Frontend  │
   └─────────────┘      └─────────────┘      └─────────────┘
```

See `docs/architecture.md` for routing logic, auth patterns, and data model.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11+, FastAPI, Pydantic v2 |
| Database | PostgreSQL 15+, SQLAlchemy 2.0 (async), Alembic |
| AI | OpenAI gpt-4.1 with function calling |
| WhatsApp | Twilio WhatsApp API |
| Frontend | Next.js 15, TypeScript, Tailwind CSS |
| Background | Redis + Celery (appointment reminders) |

## Project Structure

```
parlo/
├── app/                         # Backend
│   ├── main.py                  # FastAPI entry
│   ├── config.py                # Settings
│   ├── api/v1/                  # Endpoints (~72 routes)
│   ├── models/                  # SQLAlchemy (14 models + 2 association tables)
│   ├── schemas/                 # Pydantic schemas
│   ├── services/                # Business logic
│   ├── ai/                      # OpenAI integration
│   └── tasks/                   # Celery tasks (reminders)
├── frontend/                    # Next.js app
│   └── src/
│       ├── app/                 # Pages (13 routes)
│       ├── components/          # UI components
│       ├── lib/api/             # API client
│       └── providers/           # Auth, Location context
├── alembic/                     # Migrations
├── docs/                        # Documentation (see Documentation Map)
├── scripts/                     # Validation and utility scripts
└── tests/                       # pytest + evals
```

## Core Entities

| Entity | Purpose |
|--------|---------|
| Organization | The business (also stores onboarding state directly) |
| Location | Physical location (1+ per org) |
| Spot | Service station (chair, table) - linked to services |
| ParloUser (Staff) | Employees identified by phone (alias: Staff) |
| ServiceType | What they offer |
| EndCustomer (Customer) | End consumer (incremental identity, alias: Customer) |
| Appointment | Scheduled event |
| Conversation/Message | WhatsApp threads |
| Availability | Staff schedules |
| StaffOnboardingSession | Tracks staff WhatsApp onboarding progress |
| CustomerFlowSession | Tracks customer conversation flows (booking, cancel, etc.) |
| FunctionTrace | Function execution traces for debugging |

## Key Files

| File | What it does |
|------|--------------|
| `app/services/message_router.py` | Staff/customer routing (all 5 cases) |
| `app/services/conversation.py` | AI orchestration |
| `app/services/scheduling.py` | Availability calculation + conflict validation |
| `app/services/onboarding.py` | WhatsApp onboarding flow for new businesses |
| `app/services/customer_flows.py` | Customer booking/cancel/modify state machines |
| `app/services/handoff.py` | Handoff-to-human WhatsApp relay service |
| `app/services/staff_onboarding.py` | Staff WhatsApp onboarding flow |
| `app/ai/tools.py` | AI tool definitions + execution |
| `app/ai/prompts.py` | System prompts (Spanish) |
| `app/api/v1/simulate.py` | Simulation endpoints (admin-only) |
| `tests/evals/` | End-to-end AI eval tests |

## Development Guidelines

- All AI responses in Mexican Spanish (tu, MXN, 12-hour times)
- Every DB query must filter by `organization_id`
- Don't over-engineer — no abstractions for one-time operations
- See `docs/conventions.md` for full coding standards

## Implementation Status

**Fully implemented:** 14 models, ~72 API endpoints, admin dashboard, AI conversation handler (customer + staff + onboarding), message routing (all 5 cases), availability/conflict validation, magic link auth, schedule page, Celery reminders, WhatsApp onboarding, staff onboarding, customer flow sessions, Twilio integration + number provisioning, function tracing, handoff-to-human relay, booking notifications, business hours in prompts.

**Partial:** WhatsApp template messages, daily schedule summaries, staff conversation persistence.

**Not implemented:** Dashboard appointment modals, custom domains, customer/availability management UI, AI error recovery, row-level booking locks, Sentry integration.

## Session Workflow

**Starting:**
1. Read `workplan.md` for current status
2. Reference this file for conventions
3. See `docs/PROJECT_SPEC.md` for requirements

**Ending:**
1. Verify backend loads, frontend builds
2. Update `workplan.md` with completed tasks

## Documentation Map

| Document | What it covers |
|----------|---------------|
| `docs/PROJECT_SPEC.md` | Business requirements, user journeys, state machines |
| `docs/architecture.md` | Routing logic, auth patterns, data model, key patterns |
| `docs/testing.md` | Simulation, evals, debugging, visual verification |
| `docs/deployment.md` | Render setup, env vars, git workflow, staging/prod |
| `docs/conventions.md` | Coding standards, organization scoping, Spanish rules |
| `docs/quality.md` | Quality grades per domain and architectural layer |

## References

- [Twilio WhatsApp](https://www.twilio.com/docs/whatsapp)
- [OpenAI API](https://platform.openai.com/docs/api-reference)
- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)

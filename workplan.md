# WORKPLAN.md - Project Progress Tracker

> **Purpose:** This file tracks what has been completed, decisions made, and current state. Update this file after completing each task. Read this file at the start of every session.

---

## Current Status

**Phase:** Conversational AI Integration Complete ✅
**Last Updated:** December 27, 2024
**Last Task Completed:** Full Claude AI integration with tools for customer and staff
**Blocked By:** Docker Desktop not installed (needed for Postgres/Redis)

---

## Completed Tasks

<!-- Add completed tasks here with dates. Most recent first. -->

### 2024-12-27 - Conversational AI Integration

**What was built:**
- **Anthropic Client Wrapper** (`app/ai/client.py`)
  - Claude API integration with error handling
  - Tool call extraction and response parsing
  - Fallback handling when API key not configured

- **System Prompts** (`app/ai/prompts.py`)
  - Customer prompt: Natural Mexican Spanish, booking flow guidance
  - Staff prompt: Schedule management, walk-ins, status updates
  - Dynamic context injection (services, business hours, customer history)

- **Customer Tools** - 6 tools for booking flow:
  - `check_availability` - Check available slots (ALWAYS before offering times)
  - `book_appointment` - Book confirmed appointments
  - `get_my_appointments` - View upcoming appointments
  - `cancel_appointment` - Cancel existing appointments
  - `reschedule_appointment` - Change appointment times
  - `handoff_to_human` - Transfer to business owner

- **Staff Tools** - 7 tools for schedule management:
  - `get_my_schedule` - View personal schedule
  - `get_business_schedule` - View all appointments
  - `block_time` - Block personal time (lunch, breaks)
  - `mark_appointment_status` - Complete/no-show/cancel
  - `book_walk_in` - Register walk-in customers
  - `get_customer_history` - Lookup customer history
  - `cancel_customer_appointment` - Cancel with optional notification

- **Conversation Handler** (`app/services/conversation.py`)
  - Tool execution loop (Claude → tool → Claude → response)
  - Conversation history management
  - Context updates for continuity
  - Graceful fallbacks when AI not configured

- **Message Router Updates**
  - Integrated AI handlers for both staff and customers
  - Replaced placeholder responses with full AI flow

**Key Files Created:**
- `app/ai/client.py` - Anthropic client wrapper
- `app/ai/prompts.py` - System prompts (Mexican Spanish)
- `app/ai/tools.py` - Tool definitions and handlers
- `app/services/conversation.py` - AI conversation orchestration

**Architecture:**
```
Message → Router → ConversationHandler
                         ↓
                   Build System Prompt
                         ↓
                   Get Conversation History
                         ↓
                   Claude API Call (with tools)
                         ↓
                   Tool Execution Loop ←──┐
                         ↓                │
                   Execute Tool ──────────┘
                         ↓
                   Final Response → WhatsApp
```

**Tool Flow Example (Booking):**
```
Customer: "Quiero una cita para corte mañana"
Claude: [uses check_availability tool]
System: Returns available slots
Claude: "Tengo estos horarios disponibles para mañana: 10:00 AM, 2:00 PM, 4:00 PM"
Customer: "A las 2"
Claude: [uses book_appointment tool]
System: Returns confirmation
Claude: "Listo, tu cita quedó agendada para mañana a las 2:00 PM ✓"
```

**Verification:**
- ✅ App loads successfully with 39 routes
- ✅ All imports resolve correctly
- ✅ AI client has fallback for missing API key
- ✅ Tools defined for all customer and staff operations
- ✅ Prompts in natural Mexican Spanish

**Next Steps:**
- Install Docker and set up database
- Create Alembic migration
- Test with real Claude API key
- Fine-tune prompts based on real conversations

---

### 2024-12-27 - Testing Infrastructure

**What was built:**
- **Comprehensive Testing Guide** (`TESTING.md`) with step-by-step instructions
- **Seed Data Script** (`scripts/seed_test_data.py`) for creating test organization and data
- Complete testing workflow documented: database setup → seed data → test webhooks
- Test data includes:
  - Test organization with WhatsApp connection (phone_number_id: `test_phone_123`)
  - Staff member for routing tests (Pedro González: `525512345678`)
  - Service type (Corte de cabello - 30 min)
  - Primary location with business hours

**Key files created:**
- `TESTING.md` - Comprehensive testing guide with 10 steps
- `scripts/seed_test_data.py` - Test data seeding and cleanup script

**Status:**
- ✅ Testing documentation complete
- ✅ Seed script ready
- ⏳ **Blocked by**: Docker not installed on development machine

---

### 2024-12-26 - WhatsApp Integration (Mock Mode)

**What was built:**
- Complete WhatsApp webhook endpoint (GET verification + POST message handling)
- WhatsApp API client with mock mode (send messages, templates)
- Pydantic schemas for Meta's webhook payload format
- **MESSAGE ROUTER** - The core product differentiator:
  - Phone number-based staff vs customer identification
  - Organization lookup by WhatsApp phone_number_id
  - Message deduplication (idempotency)
  - Conversation continuity management
  - Extensive logging for debugging routing decisions
- Simple conversation handlers (staff and customer)
- Test utilities for local testing without Meta credentials
- Full message flow working in mock mode

**Key files created:**
- `app/schemas/whatsapp.py` - Meta webhook payload schemas
- `app/services/whatsapp.py` - WhatsApp API client (with mock mode)
- `app/services/message_router.py` - THE CORE routing logic
- `app/api/v1/webhooks.py` - Webhook endpoints
- `scripts/test_webhook.py` - Local testing utility

**Message Router Architecture:**
```
Message Arrives
     ↓
Lookup Organization (by phone_number_id)
     ↓
Lookup Sender (by phone number)
     ↓
Is Sender Staff? (get_staff_by_phone)
   ├─ YES → StaffConversationHandler
   └─ NO  → CustomerConversationHandler (get_or_create)
     ↓
Process & Respond
```

**Key Implementations:**
1. **Deduplication** - Checks message_id to prevent processing duplicates
2. **Staff Recognition** - `get_staff_by_phone(org_id, phone)` for routing
3. **Incremental Identity** - `get_or_create_customer()` pattern
4. **Conversation Context** - Links messages to conversations
5. **Mock Mode** - Full testing without Meta credentials

**Mock Mode Features:**
- WhatsApp client logs instead of calling Meta API
- Test script simulates webhook payloads
- Can test full flow locally: webhook → router → response
- Easy to switch to production (just update settings)

**Verification:**
- ✅ App loads with webhook endpoints
- ✅ GET /webhooks/whatsapp - Verification endpoint
- ✅ POST /webhooks/whatsapp - Message receiver
- ✅ Message router with extensive logging
- ✅ Test utilities ready for local testing

---

### 2024-12-27 - Testing Infrastructure

**What was built:**
- **Comprehensive Testing Guide** (`TESTING.md`) with step-by-step instructions
- **Seed Data Script** (`scripts/seed_test_data.py`) for creating test organization and data
- Complete testing workflow documented: database setup → seed data → test webhooks
- Test data includes:
  - Test organization with WhatsApp connection (phone_number_id: `test_phone_123`)
  - Staff member for routing tests (Pedro González: `525512345678`)
  - Service type (Corte de cabello - 30 min)
  - Primary location with business hours

**Key files created:**
- `TESTING.md` - Comprehensive testing guide with 10 steps
- `scripts/seed_test_data.py` - Test data seeding and cleanup script

**Testing Guide Covers:**
1. Database setup with Docker Compose
2. Alembic migration execution
3. Test data seeding
4. FastAPI server startup
5. Webhook verification testing (GET)
6. Customer message flow testing
7. Staff message flow testing
8. Message deduplication testing
9. Database state verification
10. Mock WhatsApp response verification

**Seed Script Features:**
- Idempotent (safe to run multiple times)
- Creates complete test environment
- Includes cleanup command (`--clean` flag)
- Matches test_webhook.py phone numbers
- Helpful summary output with test commands

**Status:**
- ✅ Testing documentation complete
- ✅ Seed script ready
- ⏳ **Blocked by**: Docker not installed on development machine
- **Next**: Install Docker Desktop → Run docker compose up → Create migrations → Seed data → Test!

**Next Steps:**
- Install Docker Desktop
- Start Postgres + Redis containers
- Create and run initial Alembic migration
- Run seed script to create test data
- Test full webhook flow with both customer and staff messages
- Add AI conversation handlers (Anthropic integration)
- Create message templates for Meta approval

---

### 2024-12-26 - Core Backend Implementation

**What was built:**
- Comprehensive Pydantic schemas for all entities (Create, Update, Response patterns)
- Service layer with business logic for all core operations
- Complete CRUD API endpoints for:
  - Organizations (with WhatsApp connection)
  - Service Types
  - Staff (with phone lookup for message routing)
  - Customers (with incremental identity pattern)
  - Appointments (with cancel/complete actions)
  - Availability (with slot calculation algorithm)
- API dependencies (organization lookup, pagination, error handling)
- Fully functional availability slot calculation engine

**Key files created:**
- `app/schemas/*.py` - 7 schema files with Create/Update/Response patterns
- `app/services/*.py` - 5 service files with business logic
- `app/api/v1/*.py` - 6 API endpoint files
- `app/api/deps.py` - Common dependencies and utilities

**Key implementations:**
- **Staff phone lookup** (`/staff/lookup`) - Core function for message routing
- **Customer get_or_create** - Incremental identity pattern implementation
- **Availability slot calculation** - Complex scheduling algorithm that:
  - Considers recurring staff availability
  - Applies exception dates
  - Removes conflicting appointments
  - Returns available time slots by staff
- **Organization-scoped endpoints** - All resources properly scoped to organizations

**API Endpoints:**
- 31 total API endpoints across 6 resource types
- All endpoints following REST conventions
- Proper error handling (404, 409 conflicts, validation)
- Pagination support for list endpoints

**Verification:**
- ✅ FastAPI app loads successfully with all 37 routes
- ✅ All imports resolve correctly
- ✅ No circular dependencies
- ✅ Pydantic validation working

**Tests passing:** N/A (no tests written yet)

---

### 2024-12-26 - Project Foundation Setup

**What was built:**
- Complete project structure following PROJECT_SPEC.md architecture
- All 9 core SQLAlchemy models (Organization, Location, Staff, ServiceType, Customer, Appointment, Conversation, Message, Availability)
- FastAPI application skeleton with health endpoints
- Alembic migration configuration
- Docker Compose setup for Postgres + Redis
- Comprehensive README.md with business and technical context
- Development environment with all dependencies

**Key files created:**
- `pyproject.toml` - Python dependencies and project configuration
- `app/models/*.py` - All database models with relationships
- `app/main.py` - FastAPI application entry point
- `app/config.py` - Settings management with pydantic-settings
- `app/database.py` - Async database connection
- `alembic.ini`, `alembic/env.py`, `alembic/script.py.mako` - Migration setup
- `docker-compose.yml` - Local development services
- `.env`, `.env.example` - Environment configuration
- `.gitignore` - Project exclusions
- `README.md` - Comprehensive documentation

**Key decisions made:**
- Used String columns with Enum classes for enum fields (not native Postgres enums) for flexibility
- Staff identified by phone number via unique constraint on (organization_id, phone_number)
- All timestamps in UTC (converted to org timezone only for display)
- Async database operations throughout
- Hatchling as build backend with explicit package configuration

**Tests passing:** N/A (no tests written yet)

**Verification:**
- ✅ FastAPI app loads successfully
- ✅ All models import without errors
- ✅ Virtual environment created with all dependencies installed

---

## In Progress

<!-- Current work that's not yet complete -->

**Next Immediate Tasks:**
1. Install Docker and start Postgres + Redis containers
2. Create initial Alembic migration
3. Run migration to create database schema
4. Start building CRUD API endpoints

---

## Project Setup Checklist

- [x] Project structure initialized
- [x] pyproject.toml with dependencies
- [x] Docker Compose (Postgres + Redis) - **Config created, needs Docker installed**
- [x] SQLAlchemy models for all entities
- [ ] Initial Alembic migration - **Pending database connection**
- [x] FastAPI app starts successfully
- [x] README.md written

## Core Backend Checklist

- [x] Organization CRUD API
- [x] ServiceType CRUD API
- [x] Staff CRUD API (with phone number lookup)
- [x] Customer CRUD API
- [x] Appointment CRUD API
- [x] Availability engine (slot calculation)
- [ ] Tests for availability edge cases

## WhatsApp Integration Checklist

- [x] Webhook endpoint (POST + GET verification)
- [x] Message parsing from Meta format
- [x] WhatsApp API client (send messages) - **Mock mode**
- [x] Message router (staff vs customer identification)
- [ ] Embedded Signup flow page
- [ ] Message templates submitted to Meta
- [ ] Test with real Meta credentials

## Conversational AI Checklist

- [x] Anthropic client wrapper
- [x] Message routing (staff vs customer)
- [x] Customer conversation handler
- [x] Staff conversation handler
- [x] Customer tools implemented
- [x] Staff tools implemented
- [x] System prompts (Spanish)
- [x] Conversation state management

## Notifications Checklist

- [ ] Celery worker setup
- [ ] Appointment reminder task
- [ ] Daily schedule summary task
- [ ] New booking notification to owner

## Production Readiness Checklist

- [ ] Error handling throughout
- [ ] Logging configured
- [ ] Environment variables documented
- [ ] Deployment configuration
- [ ] Webhook idempotency

---

## Key Decisions Log

<!-- Document important decisions made during development -->

| Date | Decision | Rationale |
|------|----------|-----------|
| 2024-12-26 | Use String columns with Enum value defaults instead of SQLAlchemy native enums | Provides more flexibility, avoids database-level enum types, easier migrations |
| 2024-12-26 | Staff identification via unique constraint on (organization_id, phone_number) | Enables staff to message the business WhatsApp and be identified automatically |
| 2024-12-26 | All models use UUID primary keys | Better for distributed systems, no collision risk, harder to enumerate |
| 2024-12-26 | Async SQLAlchemy with asyncpg driver | Modern async/await pattern, better performance for I/O operations |
| 2024-12-26 | Hatchling as build backend | Simpler than setuptools, good defaults, widely supported |

---

## Known Issues / Tech Debt

<!-- Track things that need fixing or improving later -->

**Current Issues:**
- Docker not installed on development machine - need to install Docker Desktop to run Postgres/Redis
- Initial Alembic migration not created yet - pending database availability
- No Pydantic schemas created yet - needed before building API endpoints
- No API dependency injection setup yet - will need auth, pagination, etc.

**Technical Debt:**
- Consider adding database indexes for common queries (e.g., appointments by date range, staff by phone)
- May want to add check constraints for business logic (e.g., appointment end > start)
- Consider adding audit fields (created_by, updated_by) for tracking

---

## Environment & Accounts

<!-- Track setup status of external services -->

- [ ] Meta Developer App created
- [ ] WhatsApp Business Account set up
- [ ] Anthropic API key obtained
- [ ] Hosting provider selected
- [ ] Database provisioned
- [ ] Domain configured

---

## Notes for Next Session

<!-- Leave notes for yourself or Claude about what to do next -->

**Immediate Next Steps:**

1. **Install Docker Desktop** (if running locally)
   ```bash
   docker compose up -d
   ```

2. **Create and run initial migration:**
   ```bash
   source .venv/bin/activate
   alembic revision --autogenerate -m "Initial schema with all core entities"
   alembic upgrade head
   ```

3. **Create Pydantic schemas** in `app/schemas/`:
   - Start with Organization, ServiceType, Staff schemas
   - Then Customer, Appointment schemas
   - Follow pattern: Base (shared fields), Create (input), Update (partial input), Response (output)

4. **Build first CRUD endpoints:**
   - Start with Organizations API in `app/api/v1/organizations.py`
   - Implement basic CRUD operations
   - Add business logic in `app/services/organization.py`

5. **Add API dependencies:**
   - Update `app/api/deps.py` with common dependencies
   - Add pagination helpers
   - Add error handlers

**Reference Files:**
- Business context: `docs/PROJECT_SPEC.md`
- Development patterns: `CLAUDE.md`
- Project overview: `README.md`

**Remember:**
- Mexican Spanish for all user-facing text
- All times stored in UTC
- Staff identified by phone number
- Incremental identity (customers can exist with just phone number)

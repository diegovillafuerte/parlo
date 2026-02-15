# Parlo Workplan

## Last Updated
2026-02-15

## Recently Completed

### Handoff-to-Human WhatsApp Relay (2026-02-15)
Full bidirectional WhatsApp relay when customers explicitly request to speak to a human.

**What was built:**
- `app/services/handoff.py` — Core relay service (initiate, relay, classify intent, end, timeout)
- AI tool `handoff_to_human` now actually notifies the owner and sets up relay
- Message router intercepts Cases 4 & 5 during active handoff for relay
- LLM intent classifier (gpt-4.1-nano) detects when owner wants to end vs relay
- 30-minute auto-timeout via Celery task
- Guard rails: handoff only triggers on explicit customer request, never proactively

**Files changed:** `app/services/handoff.py` (new), `app/ai/tools.py`, `app/ai/prompts.py`, `app/services/customer_flows.py`, `app/services/message_router.py`, `app/tasks/celery_app.py`, `app/tasks/cleanup.py`

**Tested on staging:** All 7 scenarios passed (initiate, customer relay, owner relay, end handoff, AI resume, second handoff while busy, timeout)

**Deployed to production:** 2026-02-15

### New Booking Notifications to Owner (2026-02-15)
Owner receives WhatsApp notification when AI books an appointment.

### Business Hours in AI Prompts (2026-02-15)
AI prompts now use actual location business hours instead of a placeholder.

## In Progress
Nothing currently in progress.

## Pending / Next Up

### High Priority
- **Staff conversation persistence** — Each staff message starts fresh with no history. Need to load recent messages into AI context like customer flows do.
- **WhatsApp template messages** — Currently falls back to regular text. Need Twilio Content API setup for structured messages (appointment confirmations, reminders).

### Medium Priority
- **Daily schedule summaries** — Send owners/staff a morning summary of their day's appointments via WhatsApp.
- **send_message_to_customer AI tool** — Allow staff to send messages to customers through the AI interface.
- **Customer management page** — Frontend UI for the existing customer API.
- **Availability management UI** — Frontend UI for the existing availability API.

### Lower Priority
- **Create/Edit appointment modals in dashboard** — Most bookings happen via WhatsApp, but dashboard editing would be useful.
- **AI error recovery** — Retry logic for OpenAI API failures.
- **Row-level locking for booking** — Race condition risk on concurrent bookings.
- **Custom domain configuration** — api.parlo.mx, app.parlo.mx
- **Sentry/error tracking integration**

## Known Issues
- Local pytest requires postgres with "postgres" role — may fail on macOS without it (37 DB-dependent tests error out locally, pass in CI)
- Admin password for production is only in Render dashboard, not in local .env
- `lib/` in .gitignore was trapping `frontend/src/lib/` — fixed with leading slash `/lib/`

## Unstaged Changes on Main
The following files have pre-existing uncommitted changes unrelated to recent work:
- `app/schemas/admin.py`
- `app/services/admin.py`
- `app/services/onboarding.py`
- `frontend/src/app/admin/organizations/[id]/page.tsx`
- `frontend/src/app/admin/organizations/page.tsx`
- `frontend/src/lib/types.ts`

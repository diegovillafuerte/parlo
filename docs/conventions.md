# Coding Conventions

## Spanish Only

All AI responses must be in Mexican Spanish:
- Use "tu" not "usted"
- Currency: MXN, prices as "$150"
- Dates: "viernes 15 de enero"
- Times: "3:00 PM" (12-hour format)

## Organization Scoping

Every database query in service and API layers **must** filter by `organization_id` to prevent data leakage between businesses. This is the most critical security invariant.

```python
# CORRECT
result = await db.execute(
    select(Appointment).where(
        Appointment.organization_id == org_id,
        Appointment.id == appointment_id,
    )
)

# WRONG - leaks data across organizations
result = await db.execute(
    select(Appointment).where(Appointment.id == appointment_id)
)
```

## Avoid Over-Engineering

- No abstractions for one-time operations
- Simple solutions over complex patterns
- Don't add features beyond what's requested
- Three similar lines of code is better than a premature abstraction

## File Size

No single Python file should exceed 2000 lines. If a file grows beyond this, split it into focused modules.

## Testing Conventions

- Use pytest with async support (`asyncio_mode = "auto"`)
- Mock external APIs (Twilio, OpenAI) in unit tests
- Test availability edge cases thoroughly
- See `docs/testing.md` for simulation and eval details

## Observability

Public functions in key service files should use the `@traced` decorator for function-level tracing:

```python
from app.services.tracing import traced

@traced
async def handle_booking(db, org_id, customer_id, ...):
    ...
```

Key service files that should have tracing:
- `app/services/message_router.py`
- `app/services/conversation.py`
- `app/services/onboarding.py`
- `app/services/customer_flows.py`
- `app/services/handoff.py`
- `app/services/staff_onboarding.py`
- `app/services/scheduling.py`

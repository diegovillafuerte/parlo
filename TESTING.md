# Testing Guide - WhatsApp Integration

This guide explains how to test the WhatsApp webhook integration locally in mock mode.

## Prerequisites

Before testing, ensure you have:

1. **Docker Desktop installed** (required for Postgres + Redis)
2. **Python virtual environment activated**
   ```bash
   source .venv/bin/activate
   ```
3. **Environment variables configured** (`.env` file with `MOCK_MODE=true`)

## Step 1: Start Database Services

Start Postgres and Redis using Docker Compose:

```bash
docker compose up -d
```

Verify services are running:
```bash
docker compose ps
```

You should see:
- `yume-postgres-1` running on port 5432
- `yume-redis-1` running on port 6379

## Step 2: Create Database Schema

Run Alembic migrations to create all tables:

```bash
# Create initial migration (first time only)
alembic revision --autogenerate -m "Initial schema with all core entities"

# Apply migrations
alembic upgrade head
```

Verify tables were created:
```bash
docker compose exec postgres psql -U postgres -d yume -c "\dt"
```

You should see tables for: organizations, locations, staff, service_types, customers, appointments, conversations, messages, availability, etc.

## Step 3: Seed Test Data

Create test organization and staff member for routing tests:

```bash
python scripts/seed_test_data.py
```

This creates:
- **Test Organization** with WhatsApp phone_number_id: `test_phone_123`
- **Staff Member** (Pedro González) with phone: `525512345678`
- **Service Type** (Corte de cabello) - 30 minutes duration

## Step 4: Start FastAPI Server

Start the development server:

```bash
uvicorn app.main:app --reload --log-level debug
```

The server should start on `http://localhost:8000`

Verify endpoints are loaded:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://localhost:8000
```

## Step 5: Test Webhook Verification (GET)

Test Meta's webhook verification:

```bash
curl "http://localhost:8000/api/v1/webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=yume-webhook-token&hub.challenge=test123"
```

**Expected Response:**
```
test123
```

**What This Tests:**
- Webhook endpoint responds to Meta's verification request
- Verify token matching works correctly
- Returns challenge string as required by Meta

## Step 6: Test Customer Message Flow

Test a message from a new customer (not registered as staff):

```bash
python scripts/test_webhook.py --customer "Hola, quiero una cita para corte de cabello" \
  --phone "525587654321" \
  --name "Juan Pérez"
```

**Expected Logs (watch server output):**

```
📬 Webhook received: whatsapp_business_account
🔍 Looking up organization by phone_number_id: test_phone_123
✅ Found organization: Test Salon (ID: xxx)
🔍 Checking if sender is staff: 525587654321
👤 Sender is NOT staff, treating as customer
🆕 Creating new customer: Juan Pérez (525587654321)
💬 Creating/continuing conversation for customer
📝 Saving message to database
🤖 Routing to CUSTOMER handler
📤 Customer conversation: Hola, quiero una cita para corte de cabello
```

**Expected Response:**
```json
{"status": "ok"}
```

**What This Tests:**
- Webhook payload parsing
- Organization lookup by phone_number_id
- Staff identification (correctly identifies as NOT staff)
- Customer creation with incremental identity
- Conversation continuity (new conversation created)
- Message storage in database
- Customer conversation handler invocation

## Step 7: Test Staff Message Flow

Test a message from a registered staff member:

```bash
python scripts/test_webhook.py --staff "Qué tengo hoy?" \
  --phone "525512345678" \
  --name "Pedro González"
```

**Expected Logs:**

```
📬 Webhook received: whatsapp_business_account
🔍 Looking up organization by phone_number_id: test_phone_123
✅ Found organization: Test Salon (ID: xxx)
🔍 Checking if sender is staff: 525512345678
👨‍💼 Sender IS staff: Pedro González (ID: xxx)
💬 Creating/continuing conversation for staff
📝 Saving message to database
🤖 Routing to STAFF handler
📤 Staff conversation: Qué tengo hoy?
```

**Expected Response:**
```json
{"status": "ok"}
```

**What This Tests:**
- Staff identification by phone number
- Correct routing to staff handler (different from customer)
- Staff conversation management
- Message storage with staff context

## Step 8: Test Message Deduplication

Send the same message twice (same message_id):

```bash
# First send
python scripts/test_webhook.py --customer "Test mensaje" --phone "525587654321"

# Second send (same message_id will be generated)
python scripts/test_webhook.py --customer "Test mensaje" --phone "525587654321"
```

**Expected Logs (second attempt):**

```
⚠️  Message already processed: wamid_test_xxx
🚫 Skipping duplicate message
```

**What This Tests:**
- Message deduplication prevents processing the same message twice
- Idempotency via message_id checking

## Step 9: Verify Database State

Check that messages and conversations were created:

```bash
docker compose exec postgres psql -U postgres -d yume -c \
  "SELECT id, phone_number, name FROM customers ORDER BY created_at DESC LIMIT 5;"

docker compose exec postgres psql -U postgres -d yume -c \
  "SELECT id, customer_id, staff_id, last_message_at FROM conversations ORDER BY created_at DESC LIMIT 5;"

docker compose exec postgres psql -U postgres -d yume -c \
  "SELECT id, conversation_id, content, direction FROM messages ORDER BY created_at DESC LIMIT 5;"
```

**Expected Results:**
- Customers table shows created customers
- Conversations table shows active conversations
- Messages table shows all sent messages with correct direction (inbound)

## Step 10: Test Mock WhatsApp Responses

The mock WhatsApp client logs outbound messages instead of sending to Meta API.

**Check server logs for:**

```
📱 [MOCK] Sending WhatsApp message to 525587654321
📱 [MOCK] Message: Hola! Gracias por contactarnos...
```

**What This Tests:**
- WhatsApp client correctly formats outbound messages
- Mock mode prevents actual API calls
- Response messages are generated and logged

## Troubleshooting

### Database Connection Failed

**Error:** `sqlalchemy.exc.OperationalError: could not connect to server`

**Solution:**
```bash
# Check if Postgres is running
docker compose ps

# Restart services if needed
docker compose restart postgres

# Check logs
docker compose logs postgres
```

### Organization Not Found

**Error:** `Organization not found for phone_number_id: test_phone_123`

**Solution:**
```bash
# Run seed script to create test data
python scripts/seed_test_data.py

# Or create manually via API
curl -X POST http://localhost:8000/api/v1/organizations \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Salon", "whatsapp_phone_number_id": "test_phone_123"}'
```

### Staff Not Recognized

**Error:** Staff messages being routed as customer messages

**Solution:**
```bash
# Verify staff exists with correct phone number
curl "http://localhost:8000/api/v1/organizations/{org_id}/staff/lookup?phone_number=525512345678"

# Create staff member via API if needed
curl -X POST http://localhost:8000/api/v1/organizations/{org_id}/staff \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Pedro González",
    "phone_number": "525512345678",
    "role": "barber",
    "is_active": true
  }'
```

### Webhook Returns Error

**Error:** `{"status": "error", "message": "..."}`

**Solution:**
- Check server logs for detailed error traceback
- Verify webhook payload format matches Meta's specification
- Ensure all required fields are present in the test payload

## Next Steps After Testing

Once local testing is complete:

1. **Get Meta Credentials:**
   - Create Meta Developer App
   - Get WhatsApp Business Account
   - Obtain Access Token, App ID, App Secret

2. **Update Environment Variables:**
   ```env
   META_APP_ID=your_app_id
   META_APP_SECRET=your_app_secret
   META_ACCESS_TOKEN=your_access_token
   MOCK_MODE=false  # Switch to production mode
   ```

3. **Deploy to Production:**
   - Set up hosting on Render (see render.yaml for Infrastructure as Code)
   - Configure webhook URL in Meta Developer Console
   - Test with real WhatsApp messages

4. **Add AI Conversation Handlers:**
   - Integrate Anthropic Claude API
   - Implement customer tools (book appointment, check availability)
   - Implement staff tools (view schedule, manage appointments)
   - Add Spanish system prompts

## Testing Checklist

- [ ] Docker Desktop installed and running
- [ ] Database services started (Postgres + Redis)
- [ ] Alembic migrations applied
- [ ] Test data seeded (organization + staff)
- [ ] FastAPI server running
- [ ] Webhook verification (GET) works
- [ ] Customer message creates new customer
- [ ] Customer message creates conversation
- [ ] Customer message saves to database
- [ ] Staff message identifies staff correctly
- [ ] Staff message routes to staff handler
- [ ] Message deduplication prevents duplicates
- [ ] Mock responses logged correctly
- [ ] Database state verified

## Reference Files

- **Test Script:** `scripts/test_webhook.py`
- **Webhook Endpoint:** `app/api/v1/webhooks.py`
- **Message Router:** `app/services/message_router.py` (THE CORE)
- **WhatsApp Client:** `app/services/whatsapp.py`
- **Schemas:** `app/schemas/whatsapp.py`
- **Configuration:** `app/config.py`

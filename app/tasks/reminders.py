"""Appointment reminder and confirmation tasks."""

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

# Shared translation dicts for Spanish date formatting
DAY_TRANSLATIONS = {
    "Monday": "lunes",
    "Tuesday": "martes",
    "Wednesday": "miércoles",
    "Thursday": "jueves",
    "Friday": "viernes",
    "Saturday": "sábado",
    "Sunday": "domingo",
}
MONTH_TRANSLATIONS = {
    "January": "enero",
    "February": "febrero",
    "March": "marzo",
    "April": "abril",
    "May": "mayo",
    "June": "junio",
    "July": "julio",
    "August": "agosto",
    "September": "septiembre",
    "October": "octubre",
    "November": "noviembre",
    "December": "diciembre",
}


def _translate_date(date_str: str) -> str:
    """Translate English day/month names to Spanish."""
    for eng, esp in DAY_TRANSLATIONS.items():
        date_str = date_str.replace(eng, esp)
    for eng, esp in MONTH_TRANSLATIONS.items():
        date_str = date_str.replace(eng, esp)
    return date_str


# ---------------------------------------------------------------------------
# 24h Confirmation (interactive)
# ---------------------------------------------------------------------------


@celery_app.task(name="app.tasks.reminders.check_and_send_confirmations")
def check_and_send_confirmations() -> dict:
    """Periodic task to send 24h confirmations for upcoming appointments.

    Runs every 5 minutes via Celery Beat.
    Finds appointments starting in 23-25 hours that haven't had confirmations sent.
    """
    import asyncio

    async def _check():
        from sqlalchemy import and_, select
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

        from app.config import get_settings
        from app.models import Appointment, AppointmentStatus

        settings = get_settings()
        engine = create_async_engine(settings.async_database_url)
        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        now = datetime.now(UTC)
        window_start = now + timedelta(hours=23)
        window_end = now + timedelta(hours=25)

        async with session_factory() as db:
            query = select(Appointment).where(
                and_(
                    Appointment.scheduled_start >= window_start,
                    Appointment.scheduled_start <= window_end,
                    Appointment.status.in_(
                        [AppointmentStatus.PENDING.value, AppointmentStatus.CONFIRMED.value]
                    ),
                    Appointment.confirmation_sent_at.is_(None),
                )
            )
            result = await db.execute(query)
            appointments = result.scalars().all()

            sent_count = 0
            for appointment in appointments:
                send_appointment_confirmation.delay(str(appointment.id))
                sent_count += 1

            return {"checked": len(appointments), "queued": sent_count}

        await engine.dispose()

    return asyncio.run(_check())


@celery_app.task(name="app.tasks.reminders.send_appointment_confirmation")
def send_appointment_confirmation(appointment_id: str) -> dict:
    """Send 24h confirmation for a specific appointment and create a flow session."""
    import asyncio

    async def _send():
        from sqlalchemy import select
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
        from sqlalchemy.orm import joinedload

        from app.config import get_settings
        from app.models import Appointment, Conversation, CustomerFlowSession
        from app.models.customer_flow_session import CustomerFlowState, CustomerFlowType
        from app.services.whatsapp import WhatsAppClient, resolve_whatsapp_sender

        settings = get_settings()
        engine = create_async_engine(settings.async_database_url)
        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        apt_uuid = UUID(appointment_id)

        async with session_factory() as db:
            query = (
                select(Appointment)
                .options(
                    joinedload(Appointment.end_customer),
                    joinedload(Appointment.organization),
                    joinedload(Appointment.service_type),
                )
                .where(Appointment.id == apt_uuid)
            )
            result = await db.execute(query)
            appointment = result.scalar_one_or_none()

            if not appointment:
                logger.error(f"Appointment {appointment_id} not found")
                return {"success": False, "error": "Appointment not found"}

            if appointment.confirmation_sent_at:
                logger.info(f"Confirmation already sent for appointment {appointment_id}")
                return {"success": False, "error": "Confirmation already sent"}

            customer = appointment.end_customer
            organization = appointment.organization
            service_type = appointment.service_type

            if not customer or not customer.phone_number:
                logger.error(f"No customer phone for appointment {appointment_id}")
                return {"success": False, "error": "No customer phone"}

            if customer.phone_number.startswith("walk_in_"):
                return {"success": False, "error": "Walk-in customer"}

            # Format date/time in org timezone
            import pytz

            org_tz = pytz.timezone(organization.timezone)
            local_time = appointment.scheduled_start.astimezone(org_tz)
            time_str = local_time.strftime("%I:%M %p").lower().lstrip("0")
            date_str = _translate_date(local_time.strftime("%A %d de %B"))

            customer_name = customer.name or "cliente"
            service_name = service_type.name if service_type else "tu cita"

            # Send confirmation message
            whatsapp = WhatsAppClient(mock_mode=not settings.twilio_account_sid)
            try:
                from_number = (
                    resolve_whatsapp_sender(organization) or settings.twilio_whatsapp_number
                )
                if not from_number:
                    logger.error("No WhatsApp sender number configured")
                    return {"success": False, "error": "No WhatsApp sender configured"}

                await whatsapp.send_confirmation_message(
                    to=customer.phone_number,
                    customer_name=customer_name,
                    service_name=service_name,
                    date_str=date_str,
                    time_str=time_str,
                    business_name=organization.name,
                    from_number=from_number,
                )
                logger.info(f"Sent 24h confirmation to {customer.phone_number}")
            except Exception as e:
                logger.error(f"Failed to send confirmation via WhatsApp: {e}")
                return {"success": False, "error": str(e)}
            finally:
                await whatsapp.close()

            # Find existing conversation for this customer+org
            conv_result = await db.execute(
                select(Conversation).where(
                    Conversation.end_customer_id == customer.id,
                    Conversation.organization_id == organization.id,
                )
            )
            conversation = conv_result.scalar_one_or_none()

            if conversation:
                # Deactivate any existing active flow sessions for this conversation
                existing_sessions_result = await db.execute(
                    select(CustomerFlowSession).where(
                        CustomerFlowSession.conversation_id == conversation.id,
                        CustomerFlowSession.is_active == True,
                    )
                )
                for existing in existing_sessions_result.scalars().all():
                    existing.is_active = False

                # Create confirmation flow session
                flow_session = CustomerFlowSession(
                    conversation_id=conversation.id,
                    end_customer_id=customer.id,
                    organization_id=organization.id,
                    flow_type=CustomerFlowType.CONFIRMATION.value,
                    state=CustomerFlowState.AWAITING_CONFIRMATION.value,
                    is_active=True,
                    collected_data={"appointment_id": str(appointment.id)},
                    last_message_at=datetime.now(UTC),
                )
                db.add(flow_session)

            # Mark confirmation as sent
            appointment.confirmation_sent_at = datetime.now(UTC)
            await db.commit()

            return {"success": True, "phone": customer.phone_number}

        await engine.dispose()

    return asyncio.run(_send())


# ---------------------------------------------------------------------------
# 1h Short Reminder (staff + customer)
# ---------------------------------------------------------------------------


@celery_app.task(name="app.tasks.reminders.check_and_send_short_reminders")
def check_and_send_short_reminders() -> dict:
    """Periodic task to send 1h reminders for upcoming appointments.

    Runs every 5 minutes via Celery Beat.
    Finds appointments starting in 55-65 minutes that haven't had reminders sent.
    """
    import asyncio

    async def _check():
        from sqlalchemy import and_, select
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

        from app.config import get_settings
        from app.models import Appointment, AppointmentStatus

        settings = get_settings()
        engine = create_async_engine(settings.async_database_url)
        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        now = datetime.now(UTC)
        window_start = now + timedelta(minutes=55)
        window_end = now + timedelta(minutes=65)

        async with session_factory() as db:
            query = select(Appointment).where(
                and_(
                    Appointment.scheduled_start >= window_start,
                    Appointment.scheduled_start <= window_end,
                    Appointment.status.in_(
                        [AppointmentStatus.PENDING.value, AppointmentStatus.CONFIRMED.value]
                    ),
                    Appointment.reminder_sent_at.is_(None),
                )
            )
            result = await db.execute(query)
            appointments = result.scalars().all()

            sent_count = 0
            for appointment in appointments:
                send_short_reminder.delay(str(appointment.id))
                sent_count += 1

            return {"checked": len(appointments), "queued": sent_count}

        await engine.dispose()

    return asyncio.run(_check())


@celery_app.task(name="app.tasks.reminders.send_short_reminder")
def send_short_reminder(appointment_id: str) -> dict:
    """Send 1h reminder to both customer and assigned staff."""
    import asyncio

    async def _send():
        from sqlalchemy import select
        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
        from sqlalchemy.orm import joinedload

        from app.config import get_settings
        from app.models import Appointment
        from app.services.whatsapp import WhatsAppClient, resolve_whatsapp_sender

        settings = get_settings()
        engine = create_async_engine(settings.async_database_url)
        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        apt_uuid = UUID(appointment_id)

        async with session_factory() as db:
            query = (
                select(Appointment)
                .options(
                    joinedload(Appointment.end_customer),
                    joinedload(Appointment.organization),
                    joinedload(Appointment.service_type),
                    joinedload(Appointment.parlo_user),
                )
                .where(Appointment.id == apt_uuid)
            )
            result = await db.execute(query)
            appointment = result.scalar_one_or_none()

            if not appointment:
                logger.error(f"Appointment {appointment_id} not found")
                return {"success": False, "error": "Appointment not found"}

            if appointment.reminder_sent_at:
                logger.info(f"Short reminder already sent for appointment {appointment_id}")
                return {"success": False, "error": "Reminder already sent"}

            customer = appointment.end_customer
            organization = appointment.organization
            service_type = appointment.service_type
            staff = appointment.parlo_user

            # Format time in org timezone
            import pytz

            org_tz = pytz.timezone(organization.timezone)
            local_time = appointment.scheduled_start.astimezone(org_tz)
            time_str = local_time.strftime("%I:%M %p").lower().lstrip("0")

            service_name = service_type.name if service_type else "tu cita"

            whatsapp = WhatsAppClient(mock_mode=not settings.twilio_account_sid)
            from_number = resolve_whatsapp_sender(organization) or settings.twilio_whatsapp_number
            if not from_number:
                logger.error("No WhatsApp sender number configured for short reminders")
                return {"success": False, "error": "No WhatsApp sender configured"}

            try:
                # Send to customer
                if (
                    customer
                    and customer.phone_number
                    and not customer.phone_number.startswith("walk_in_")
                ):
                    customer_name = customer.name or "cliente"
                    customer_msg = (
                        f"\u00a1Hola {customer_name}! Tu cita de {service_name} "
                        f"es en 1 hora a las {time_str} en {organization.name}. "
                        f"\u00a1Te esperamos!"
                    )
                    try:
                        await whatsapp.send_text_message(
                            phone_number_id=from_number,
                            to=customer.phone_number,
                            message=customer_msg,
                            from_number=from_number,
                        )
                        logger.info(f"Sent 1h reminder to customer {customer.phone_number}")
                    except Exception as e:
                        logger.error(f"Failed to send 1h reminder to customer: {e}")

                # Send to assigned staff
                if staff and staff.phone_number:
                    customer_display = customer.name if customer and customer.name else "un cliente"
                    staff_msg = (
                        f"Tienes una cita de {service_name} con {customer_display} "
                        f"en 1 hora a las {time_str}."
                    )
                    try:
                        await whatsapp.send_text_message(
                            phone_number_id=from_number,
                            to=staff.phone_number,
                            message=staff_msg,
                            from_number=from_number,
                        )
                        logger.info(f"Sent 1h reminder to staff {staff.name}")
                    except Exception as e:
                        logger.error(f"Failed to send 1h reminder to staff: {e}")
            finally:
                await whatsapp.close()

            # Mark reminder as sent
            appointment.reminder_sent_at = datetime.now(UTC)
            await db.commit()

            return {"success": True}

        await engine.dispose()

    return asyncio.run(_send())

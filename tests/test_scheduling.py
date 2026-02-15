"""Tests for appointment conflict detection."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Appointment,
    AppointmentSource,
    AppointmentStatus,
    Customer,
    Location,
    Organization,
    ServiceType,
    Spot,
    Staff,
)
from app.services import scheduling as scheduling_service


# Helper to create appointments
async def create_appointment(
    db: AsyncSession,
    organization: Organization,
    location: Location,
    customer: Customer,
    service_type: ServiceType,
    staff: Staff | None,
    spot: Spot | None,
    start_time: datetime,
    end_time: datetime,
    status: str = AppointmentStatus.CONFIRMED.value,
) -> Appointment:
    """Create a test appointment."""
    appointment = Appointment(
        id=uuid4(),
        organization_id=organization.id,
        location_id=location.id,
        end_customer_id=customer.id,
        service_type_id=service_type.id,
        parlo_user_id=staff.id if staff else None,
        spot_id=spot.id if spot else None,
        scheduled_start=start_time,
        scheduled_end=end_time,
        status=status,
        source=AppointmentSource.WHATSAPP.value,
    )
    db.add(appointment)
    await db.flush()
    return appointment


class TestCheckAppointmentConflicts:
    """Tests for check_appointment_conflicts function."""

    @pytest.mark.asyncio
    async def test_no_conflict_different_times(
        self,
        db: AsyncSession,
        organization: Organization,
        location: Location,
        customer: Customer,
        service_type: ServiceType,
        staff: Staff,
    ):
        """Test no conflict when times don't overlap."""
        # Create existing appointment at 10:00-10:30
        existing_start = datetime(2024, 1, 15, 10, 0, tzinfo=UTC)
        existing_end = datetime(2024, 1, 15, 10, 30, tzinfo=UTC)
        await create_appointment(
            db,
            organization,
            location,
            customer,
            service_type,
            staff,
            None,
            existing_start,
            existing_end,
        )

        # Check for conflict at 11:00-11:30 (no overlap)
        new_start = datetime(2024, 1, 15, 11, 0, tzinfo=UTC)
        new_end = datetime(2024, 1, 15, 11, 30, tzinfo=UTC)

        conflicts = await scheduling_service.check_appointment_conflicts(
            db=db,
            organization_id=organization.id,
            staff_id=staff.id,
            spot_id=None,
            start_time=new_start,
            end_time=new_end,
        )

        assert len(conflicts) == 0

    @pytest.mark.asyncio
    async def test_staff_conflict_exact_same_time(
        self,
        db: AsyncSession,
        organization: Organization,
        location: Location,
        customer: Customer,
        service_type: ServiceType,
        staff: Staff,
    ):
        """Test conflict when times are exactly the same."""
        start_time = datetime(2024, 1, 15, 10, 0, tzinfo=UTC)
        end_time = datetime(2024, 1, 15, 10, 30, tzinfo=UTC)

        existing = await create_appointment(
            db, organization, location, customer, service_type, staff, None, start_time, end_time
        )

        conflicts = await scheduling_service.check_appointment_conflicts(
            db=db,
            organization_id=organization.id,
            staff_id=staff.id,
            spot_id=None,
            start_time=start_time,
            end_time=end_time,
        )

        assert len(conflicts) == 1
        assert conflicts[0].id == existing.id

    @pytest.mark.asyncio
    async def test_staff_conflict_new_starts_during_existing(
        self,
        db: AsyncSession,
        organization: Organization,
        location: Location,
        customer: Customer,
        service_type: ServiceType,
        staff: Staff,
    ):
        """Test conflict when new appointment starts during existing."""
        # Existing: 10:00-10:30
        existing_start = datetime(2024, 1, 15, 10, 0, tzinfo=UTC)
        existing_end = datetime(2024, 1, 15, 10, 30, tzinfo=UTC)
        await create_appointment(
            db,
            organization,
            location,
            customer,
            service_type,
            staff,
            None,
            existing_start,
            existing_end,
        )

        # New: 10:15-10:45 (starts during existing)
        new_start = datetime(2024, 1, 15, 10, 15, tzinfo=UTC)
        new_end = datetime(2024, 1, 15, 10, 45, tzinfo=UTC)

        conflicts = await scheduling_service.check_appointment_conflicts(
            db=db,
            organization_id=organization.id,
            staff_id=staff.id,
            spot_id=None,
            start_time=new_start,
            end_time=new_end,
        )

        assert len(conflicts) == 1

    @pytest.mark.asyncio
    async def test_staff_conflict_new_ends_during_existing(
        self,
        db: AsyncSession,
        organization: Organization,
        location: Location,
        customer: Customer,
        service_type: ServiceType,
        staff: Staff,
    ):
        """Test conflict when new appointment ends during existing."""
        # Existing: 10:00-10:30
        existing_start = datetime(2024, 1, 15, 10, 0, tzinfo=UTC)
        existing_end = datetime(2024, 1, 15, 10, 30, tzinfo=UTC)
        await create_appointment(
            db,
            organization,
            location,
            customer,
            service_type,
            staff,
            None,
            existing_start,
            existing_end,
        )

        # New: 9:45-10:15 (ends during existing)
        new_start = datetime(2024, 1, 15, 9, 45, tzinfo=UTC)
        new_end = datetime(2024, 1, 15, 10, 15, tzinfo=UTC)

        conflicts = await scheduling_service.check_appointment_conflicts(
            db=db,
            organization_id=organization.id,
            staff_id=staff.id,
            spot_id=None,
            start_time=new_start,
            end_time=new_end,
        )

        assert len(conflicts) == 1

    @pytest.mark.asyncio
    async def test_staff_conflict_new_contains_existing(
        self,
        db: AsyncSession,
        organization: Organization,
        location: Location,
        customer: Customer,
        service_type: ServiceType,
        staff: Staff,
    ):
        """Test conflict when new appointment completely contains existing."""
        # Existing: 10:00-10:30
        existing_start = datetime(2024, 1, 15, 10, 0, tzinfo=UTC)
        existing_end = datetime(2024, 1, 15, 10, 30, tzinfo=UTC)
        await create_appointment(
            db,
            organization,
            location,
            customer,
            service_type,
            staff,
            None,
            existing_start,
            existing_end,
        )

        # New: 9:30-11:00 (contains existing)
        new_start = datetime(2024, 1, 15, 9, 30, tzinfo=UTC)
        new_end = datetime(2024, 1, 15, 11, 0, tzinfo=UTC)

        conflicts = await scheduling_service.check_appointment_conflicts(
            db=db,
            organization_id=organization.id,
            staff_id=staff.id,
            spot_id=None,
            start_time=new_start,
            end_time=new_end,
        )

        assert len(conflicts) == 1

    @pytest.mark.asyncio
    async def test_spot_conflict_same_spot_same_time(
        self,
        db: AsyncSession,
        organization: Organization,
        location: Location,
        customer: Customer,
        service_type: ServiceType,
        staff: Staff,
        staff2: Staff,
        spot: Spot,
    ):
        """Test conflict when same spot is double-booked."""
        start_time = datetime(2024, 1, 15, 10, 0, tzinfo=UTC)
        end_time = datetime(2024, 1, 15, 10, 30, tzinfo=UTC)

        # Existing appointment with staff1 and spot
        await create_appointment(
            db, organization, location, customer, service_type, staff, spot, start_time, end_time
        )

        # Try to book different staff but same spot
        conflicts = await scheduling_service.check_appointment_conflicts(
            db=db,
            organization_id=organization.id,
            staff_id=staff2.id,  # Different staff
            spot_id=spot.id,  # Same spot
            start_time=start_time,
            end_time=end_time,
        )

        assert len(conflicts) == 1

    @pytest.mark.asyncio
    async def test_no_conflict_different_staff_no_spot(
        self,
        db: AsyncSession,
        organization: Organization,
        location: Location,
        customer: Customer,
        service_type: ServiceType,
        staff: Staff,
        staff2: Staff,
    ):
        """Test no conflict when different staff at same time (no spot)."""
        start_time = datetime(2024, 1, 15, 10, 0, tzinfo=UTC)
        end_time = datetime(2024, 1, 15, 10, 30, tzinfo=UTC)

        # Existing appointment with staff1
        await create_appointment(
            db, organization, location, customer, service_type, staff, None, start_time, end_time
        )

        # Check for staff2 - should not conflict
        conflicts = await scheduling_service.check_appointment_conflicts(
            db=db,
            organization_id=organization.id,
            staff_id=staff2.id,  # Different staff
            spot_id=None,
            start_time=start_time,
            end_time=end_time,
        )

        assert len(conflicts) == 0

    @pytest.mark.asyncio
    async def test_no_conflict_cancelled_appointment(
        self,
        db: AsyncSession,
        organization: Organization,
        location: Location,
        customer: Customer,
        service_type: ServiceType,
        staff: Staff,
    ):
        """Test no conflict with cancelled appointment at same time."""
        start_time = datetime(2024, 1, 15, 10, 0, tzinfo=UTC)
        end_time = datetime(2024, 1, 15, 10, 30, tzinfo=UTC)

        # Create cancelled appointment
        await create_appointment(
            db,
            organization,
            location,
            customer,
            service_type,
            staff,
            None,
            start_time,
            end_time,
            status=AppointmentStatus.CANCELLED.value,
        )

        conflicts = await scheduling_service.check_appointment_conflicts(
            db=db,
            organization_id=organization.id,
            staff_id=staff.id,
            spot_id=None,
            start_time=start_time,
            end_time=end_time,
        )

        assert len(conflicts) == 0

    @pytest.mark.asyncio
    async def test_no_conflict_completed_appointment(
        self,
        db: AsyncSession,
        organization: Organization,
        location: Location,
        customer: Customer,
        service_type: ServiceType,
        staff: Staff,
    ):
        """Test no conflict with completed appointment at same time."""
        start_time = datetime(2024, 1, 15, 10, 0, tzinfo=UTC)
        end_time = datetime(2024, 1, 15, 10, 30, tzinfo=UTC)

        # Create completed appointment
        await create_appointment(
            db,
            organization,
            location,
            customer,
            service_type,
            staff,
            None,
            start_time,
            end_time,
            status=AppointmentStatus.COMPLETED.value,
        )

        conflicts = await scheduling_service.check_appointment_conflicts(
            db=db,
            organization_id=organization.id,
            staff_id=staff.id,
            spot_id=None,
            start_time=start_time,
            end_time=end_time,
        )

        assert len(conflicts) == 0

    @pytest.mark.asyncio
    async def test_reschedule_excludes_self(
        self,
        db: AsyncSession,
        organization: Organization,
        location: Location,
        customer: Customer,
        service_type: ServiceType,
        staff: Staff,
    ):
        """Test that reschedule doesn't conflict with itself."""
        start_time = datetime(2024, 1, 15, 10, 0, tzinfo=UTC)
        end_time = datetime(2024, 1, 15, 10, 30, tzinfo=UTC)

        existing = await create_appointment(
            db, organization, location, customer, service_type, staff, None, start_time, end_time
        )

        # Reschedule to same time (exclude self)
        conflicts = await scheduling_service.check_appointment_conflicts(
            db=db,
            organization_id=organization.id,
            staff_id=staff.id,
            spot_id=None,
            start_time=start_time,
            end_time=end_time,
            exclude_appointment_id=existing.id,  # Exclude self
        )

        assert len(conflicts) == 0

    @pytest.mark.asyncio
    async def test_no_conflict_adjacent_appointments(
        self,
        db: AsyncSession,
        organization: Organization,
        location: Location,
        customer: Customer,
        service_type: ServiceType,
        staff: Staff,
    ):
        """Test no conflict for back-to-back appointments."""
        # Existing: 10:00-10:30
        existing_start = datetime(2024, 1, 15, 10, 0, tzinfo=UTC)
        existing_end = datetime(2024, 1, 15, 10, 30, tzinfo=UTC)
        await create_appointment(
            db,
            organization,
            location,
            customer,
            service_type,
            staff,
            None,
            existing_start,
            existing_end,
        )

        # New: 10:30-11:00 (starts exactly when existing ends)
        new_start = datetime(2024, 1, 15, 10, 30, tzinfo=UTC)
        new_end = datetime(2024, 1, 15, 11, 0, tzinfo=UTC)

        conflicts = await scheduling_service.check_appointment_conflicts(
            db=db,
            organization_id=organization.id,
            staff_id=staff.id,
            spot_id=None,
            start_time=new_start,
            end_time=new_end,
        )

        assert len(conflicts) == 0

    @pytest.mark.asyncio
    async def test_no_conflict_no_staff_no_spot(
        self,
        db: AsyncSession,
        organization: Organization,
    ):
        """Test returns empty when no staff_id and no spot_id provided."""
        start_time = datetime(2024, 1, 15, 10, 0, tzinfo=UTC)
        end_time = datetime(2024, 1, 15, 10, 30, tzinfo=UTC)

        conflicts = await scheduling_service.check_appointment_conflicts(
            db=db,
            organization_id=organization.id,
            staff_id=None,
            spot_id=None,
            start_time=start_time,
            end_time=end_time,
        )

        assert len(conflicts) == 0

'use client';

import { useState, useEffect, useCallback } from 'react';
import { format, addDays, subDays, startOfDay, parseISO, differenceInMinutes } from 'date-fns';
import { es } from 'date-fns/locale';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { useAuth } from '@/providers/AuthProvider';
import { getAppointments, cancelAppointment, completeAppointment, markNoShow } from '@/lib/api/appointments';
import { getStaffList } from '@/lib/api/staff';
import { Appointment, Staff } from '@/lib/types';

type ViewMode = 'calendar' | 'list';

const STATUS_LABELS: Record<string, { label: string; className: string }> = {
  pending: { label: 'Pendiente', className: 'bg-yellow-100 text-yellow-800' },
  confirmed: { label: 'Confirmada', className: 'bg-blue-100 text-blue-800' },
  completed: { label: 'Completada', className: 'bg-green-100 text-green-800' },
  cancelled: { label: 'Cancelada', className: 'bg-gray-100 text-gray-600' },
  no_show: { label: 'No asistió', className: 'bg-red-100 text-red-800' },
};

const HOUR_HEIGHT = 60; // px per hour
const START_HOUR = 8;
const END_HOUR = 20;
const TOTAL_HOURS = END_HOUR - START_HOUR;

export default function SchedulePage() {
  const { organization } = useAuth();
  const [selectedDate, setSelectedDate] = useState(startOfDay(new Date()));
  const [viewMode, setViewMode] = useState<ViewMode>('calendar');
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [staff, setStaff] = useState<Staff[]>([]);
  const [selectedStaffId, setSelectedStaffId] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const fetchAppointments = useCallback(async () => {
    if (!organization) return;

    setIsLoading(true);
    try {
      const dateStr = format(selectedDate, 'yyyy-MM-dd');
      const filters: { start_date: string; end_date: string; staff_id?: string } = {
        start_date: dateStr,
        end_date: dateStr,
      };
      if (selectedStaffId) {
        filters.staff_id = selectedStaffId;
      }
      const data = await getAppointments(organization.id, filters);
      setAppointments(data);
    } catch (error) {
      console.error('Error fetching appointments:', error);
    } finally {
      setIsLoading(false);
    }
  }, [organization, selectedDate, selectedStaffId]);

  const fetchStaff = useCallback(async () => {
    if (!organization) return;
    try {
      const data = await getStaffList(organization.id);
      setStaff(data);
    } catch (error) {
      console.error('Error fetching staff:', error);
    }
  }, [organization]);

  useEffect(() => {
    fetchAppointments();
  }, [fetchAppointments]);

  useEffect(() => {
    fetchStaff();
  }, [fetchStaff]);

  const goToPreviousDay = () => setSelectedDate(subDays(selectedDate, 1));
  const goToNextDay = () => setSelectedDate(addDays(selectedDate, 1));
  const goToToday = () => setSelectedDate(startOfDay(new Date()));

  const handleCancel = async (appointmentId: string) => {
    if (!organization) return;
    setActionLoading(appointmentId);
    try {
      await cancelAppointment(organization.id, appointmentId);
      fetchAppointments();
    } catch (error) {
      console.error('Error cancelling appointment:', error);
    } finally {
      setActionLoading(null);
    }
  };

  const handleComplete = async (appointmentId: string) => {
    if (!organization) return;
    setActionLoading(appointmentId);
    try {
      await completeAppointment(organization.id, appointmentId);
      fetchAppointments();
    } catch (error) {
      console.error('Error completing appointment:', error);
    } finally {
      setActionLoading(null);
    }
  };

  const handleNoShow = async (appointmentId: string) => {
    if (!organization) return;
    setActionLoading(appointmentId);
    try {
      await markNoShow(organization.id, appointmentId);
      fetchAppointments();
    } catch (error) {
      console.error('Error marking no-show:', error);
    } finally {
      setActionLoading(null);
    }
  };

  // Split into active vs recent changes
  const activeAppointments = appointments.filter(
    (apt) => apt.status === 'pending' || apt.status === 'confirmed'
  );
  const recentChanges = appointments.filter(
    (apt) => apt.status === 'cancelled' || apt.status === 'completed' || apt.status === 'no_show'
  );

  return (
    <DashboardLayout>
      <div className="space-y-4">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Agenda</h1>
            <p className="text-gray-600">
              {format(selectedDate, "EEEE d 'de' MMMM", { locale: es })}
            </p>
          </div>

          <div className="flex items-center gap-2">
            {/* Staff Filter */}
            <select
              value={selectedStaffId}
              onChange={(e) => setSelectedStaffId(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Todos los empleados</option>
              {staff.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>

            {/* View Toggle */}
            <div className="bg-gray-100 rounded-lg p-1 flex">
              <button
                onClick={() => setViewMode('calendar')}
                className={`px-3 py-1.5 text-sm font-medium rounded-md transition ${
                  viewMode === 'calendar'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Calendario
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`px-3 py-1.5 text-sm font-medium rounded-md transition ${
                  viewMode === 'list'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Lista
              </button>
            </div>
          </div>
        </div>

        {/* Date Navigation */}
        <div className="flex items-center justify-between bg-white rounded-lg p-4 shadow-sm">
          <button
            onClick={goToPreviousDay}
            className="p-2 hover:bg-gray-100 rounded-lg transition"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>

          <button
            onClick={goToToday}
            className="px-4 py-2 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded-lg transition"
          >
            Hoy
          </button>

          <button
            onClick={goToNextDay}
            className="p-2 hover:bg-gray-100 rounded-lg transition"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>

        {/* Recent Changes Log */}
        {!isLoading && recentChanges.length > 0 && (
          <div className="bg-white rounded-lg shadow-sm p-4">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Cambios recientes</h3>
            <div className="space-y-1">
              {recentChanges.map((apt) => (
                <div key={apt.id} className="flex items-center gap-2 text-sm">
                  <StatusBadge status={apt.status} />
                  <span className="text-gray-700">{apt.customer_name || 'Cliente'}</span>
                  <span className="text-gray-400">
                    {format(parseISO(apt.scheduled_start), 'h:mm a')}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Content */}
        {isLoading ? (
          <div className="bg-white rounded-lg shadow-sm p-8 text-center">
            <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"></div>
            <p className="mt-4 text-gray-500">Cargando citas...</p>
          </div>
        ) : viewMode === 'calendar' ? (
          <CalendarView
            date={selectedDate}
            appointments={activeAppointments}
            staff={staff}
            onCancel={handleCancel}
            actionLoading={actionLoading}
          />
        ) : (
          <ListView
            appointments={activeAppointments}
            staff={staff}
            onCancel={handleCancel}
            onComplete={handleComplete}
            onNoShow={handleNoShow}
            actionLoading={actionLoading}
          />
        )}
      </div>
    </DashboardLayout>
  );
}

interface ViewProps {
  appointments: Appointment[];
  staff: Staff[];
  onCancel: (id: string) => void;
  onComplete: (id: string) => void;
  onNoShow: (id: string) => void;
  actionLoading: string | null;
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
function CalendarView({ date, appointments, staff, onCancel, actionLoading }: { date: Date; appointments: Appointment[]; staff: Staff[]; onCancel: (id: string) => void; actionLoading: string | null }) {
  const timeLabels = Array.from({ length: TOTAL_HOURS + 1 }, (_, i) => {
    const hour = START_HOUR + i;
    return { hour, label: `${hour.toString().padStart(2, '0')}:00` };
  });

  const getStaffName = (staffId: string | null) => {
    if (!staffId) return 'Sin asignar';
    return staff.find((s) => s.id === staffId)?.name || 'Desconocido';
  };

  return (
    <div className="bg-white rounded-lg shadow-sm overflow-hidden">
      <div className="relative" style={{ height: `${TOTAL_HOURS * HOUR_HEIGHT}px` }}>
        {/* Time labels and grid lines */}
        {timeLabels.map(({ hour, label }) => {
          const top = (hour - START_HOUR) * HOUR_HEIGHT;
          return (
            <div key={label}>
              <div
                className="absolute left-0 w-16 text-sm text-gray-500 font-medium px-3 -translate-y-1/2"
                style={{ top: `${top}px` }}
              >
                {label}
              </div>
              <div
                className="absolute left-16 right-0 border-t border-gray-100"
                style={{ top: `${top}px` }}
              />
            </div>
          );
        })}

        {/* Appointment cards */}
        <div className="absolute left-16 right-0 top-0 bottom-0">
          {appointments.map((apt) => {
            const start = parseISO(apt.scheduled_start);
            const end = parseISO(apt.scheduled_end);
            const startMinutes = (start.getHours() - START_HOUR) * 60 + start.getMinutes();
            const durationMinutes = differenceInMinutes(end, start);
            const top = (startMinutes / 60) * HOUR_HEIGHT;
            const height = Math.max((durationMinutes / 60) * HOUR_HEIGHT, 24);
            const isShort = durationMinutes <= 30;

            return (
              <div
                key={apt.id}
                className="absolute left-2 right-2"
                style={{ top: `${top}px`, height: `${height}px` }}
              >
                <AppointmentCard
                  appointment={apt}
                  staffName={getStaffName(apt.staff_id)}
                  onCancel={onCancel}
                  actionLoading={actionLoading}
                  isShort={isShort}
                />
              </div>
            );
          })}
        </div>
      </div>

      {/* Empty State */}
      {appointments.length === 0 && (
        <div className="p-8 text-center text-gray-500 border-t">
          <svg className="w-12 h-12 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <p className="font-medium">No hay citas para este día</p>
          <p className="text-sm mt-1">Las citas aparecerán aquí cuando tus clientes las agenden.</p>
        </div>
      )}
    </div>
  );
}

function ListView({ appointments, staff, onCancel, onComplete, onNoShow, actionLoading }: ViewProps) {
  const getStaffName = (staffId: string | null) => {
    if (!staffId) return 'Sin asignar';
    return staff.find((s) => s.id === staffId)?.name || 'Desconocido';
  };

  // Sort by time
  const sortedAppointments = [...appointments].sort((a, b) =>
    new Date(a.scheduled_start).getTime() - new Date(b.scheduled_start).getTime()
  );

  return (
    <div className="bg-white rounded-lg shadow-sm overflow-hidden">
      {/* Table Header */}
      <div className="hidden sm:grid grid-cols-6 gap-4 px-6 py-3 bg-gray-50 text-sm font-medium text-gray-600 border-b">
        <div>Hora</div>
        <div>Cliente</div>
        <div>Servicio</div>
        <div>Empleado</div>
        <div>Estado</div>
        <div>Acciones</div>
      </div>

      {sortedAppointments.length > 0 ? (
        <div className="divide-y divide-gray-100">
          {sortedAppointments.map((apt) => (
            <div key={apt.id} className="grid grid-cols-1 sm:grid-cols-6 gap-2 sm:gap-4 px-6 py-4 hover:bg-gray-50">
              <div className="text-sm font-medium text-gray-900">
                {format(parseISO(apt.scheduled_start), 'h:mm a')} - {format(parseISO(apt.scheduled_end), 'h:mm a')}
              </div>
              <div className="text-sm text-gray-600">
                <span className="sm:hidden font-medium text-gray-500">Cliente: </span>
                {apt.customer_name || 'Cliente'}
              </div>
              <div className="text-sm text-gray-600">
                <span className="sm:hidden font-medium text-gray-500">Servicio: </span>
                {apt.service_type_name || 'Servicio'}
              </div>
              <div className="text-sm text-gray-600">
                <span className="sm:hidden font-medium text-gray-500">Empleado: </span>
                {getStaffName(apt.staff_id)}
              </div>
              <div>
                <StatusBadge status={apt.status} />
              </div>
              <div className="flex gap-2">
                <AppointmentActions
                  appointment={apt}
                  onCancel={onCancel}
                  onComplete={onComplete}
                  onNoShow={onNoShow}
                  actionLoading={actionLoading}
                />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="p-8 text-center text-gray-500">
          <svg className="w-12 h-12 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <p className="font-medium">No hay citas para mostrar</p>
          <p className="text-sm mt-1">Conecta tu WhatsApp para empezar a recibir citas.</p>
        </div>
      )}
    </div>
  );
}

function AppointmentCard({
  appointment,
  staffName,
  onCancel,
  actionLoading,
  isShort = false,
}: {
  appointment: Appointment;
  staffName: string;
  onCancel: (id: string) => void;
  actionLoading: string | null;
  isShort?: boolean;
}) {
  const startTime = format(parseISO(appointment.scheduled_start), 'h:mm a');
  const endTime = format(parseISO(appointment.scheduled_end), 'h:mm a');
  const isLoading = actionLoading === appointment.id;
  const canAct = ['pending', 'confirmed'].includes(appointment.status);

  if (isShort) {
    return (
      <div className="h-full bg-blue-50 border border-blue-200 rounded-lg px-3 py-1 flex items-center justify-between gap-2 overflow-hidden text-sm">
        <div className="flex items-center gap-2 min-w-0">
          <span className="font-medium text-gray-900 truncate">{appointment.customer_name || 'Cliente'}</span>
          <span className="text-gray-500 whitespace-nowrap">{startTime}</span>
        </div>
        {canAct && (
          <button
            onClick={() => onCancel(appointment.id)}
            disabled={isLoading}
            className="text-xs text-red-600 hover:bg-red-50 px-2 py-0.5 rounded-full border border-red-200 whitespace-nowrap disabled:opacity-50"
          >
            Cancelar
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="h-full bg-blue-50 border border-blue-200 rounded-lg p-3 overflow-hidden text-sm">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="font-medium text-gray-900 truncate">
            {appointment.customer_name || 'Cliente'}
          </div>
          <div className="text-gray-600">
            {startTime} - {endTime}
          </div>
          <div className="text-gray-500 text-xs mt-1">
            {staffName}
          </div>
        </div>
        <div className="flex flex-col items-end gap-2">
          <StatusBadge status={appointment.status} />
          {canAct && (
            <button
              onClick={() => onCancel(appointment.id)}
              disabled={isLoading}
              className="text-xs text-red-600 hover:bg-red-50 px-2 py-0.5 rounded-full border border-red-200 disabled:opacity-50"
            >
              Cancelar
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const config = STATUS_LABELS[status] || { label: status, className: 'bg-gray-100 text-gray-800' };
  return (
    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${config.className}`}>
      {config.label}
    </span>
  );
}

function AppointmentActions({
  appointment,
  onCancel,
  onComplete,
  onNoShow,
  actionLoading,
}: {
  appointment: Appointment;
  onCancel: (id: string) => void;
  onComplete: (id: string) => void;
  onNoShow: (id: string) => void;
  actionLoading: string | null;
}) {
  const isLoading = actionLoading === appointment.id;
  const canAct = ['pending', 'confirmed'].includes(appointment.status);

  if (!canAct) return null;

  return (
    <div className="flex gap-1">
      <button
        onClick={() => onComplete(appointment.id)}
        disabled={isLoading}
        className="px-2 py-1 text-xs rounded hover:bg-gray-100 disabled:opacity-50 text-green-600"
      >
        Completar
      </button>
      <button
        onClick={() => onNoShow(appointment.id)}
        disabled={isLoading}
        className="px-2 py-1 text-xs rounded hover:bg-gray-100 disabled:opacity-50 text-orange-600"
      >
        No asistió
      </button>
      <button
        onClick={() => onCancel(appointment.id)}
        disabled={isLoading}
        className="px-2 py-1 text-xs rounded hover:bg-gray-100 disabled:opacity-50 text-red-600"
      >
        Cancelar
      </button>
    </div>
  );
}

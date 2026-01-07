import api from './client';
import { Availability, AvailabilityCreate } from '@/lib/types';

export async function getStaffAvailability(
  orgId: string,
  staffId: string
): Promise<Availability[]> {
  const response = await api.get(`/organizations/${orgId}/staff/${staffId}/availability`);
  return response.data;
}

export async function createAvailability(
  orgId: string,
  staffId: string,
  data: AvailabilityCreate
): Promise<Availability> {
  const response = await api.post(`/organizations/${orgId}/staff/${staffId}/availability`, data);
  return response.data;
}

export async function deleteAvailability(
  orgId: string,
  staffId: string,
  availabilityId: string
): Promise<void> {
  await api.delete(`/organizations/${orgId}/staff/${staffId}/availability/${availabilityId}`);
}

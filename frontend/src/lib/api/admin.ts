import api from './client';
import type {
  AdminLoginResponse,
  AdminStats,
  AdminOrganizationSummary,
  AdminOrganizationDetail,
  AdminConversationSummary,
  AdminConversationDetail,
  AdminActivityItem,
  AdminImpersonateResponse,
} from '@/lib/types';

export async function adminLogin(password: string): Promise<AdminLoginResponse> {
  const response = await api.post<AdminLoginResponse>('/admin/auth/login', {
    password,
  });
  return response.data;
}

export async function getAdminStats(): Promise<AdminStats> {
  const response = await api.get<AdminStats>('/admin/stats');
  return response.data;
}

export async function listOrganizations(params?: {
  search?: string;
  status?: string;
  skip?: number;
  limit?: number;
}): Promise<AdminOrganizationSummary[]> {
  const response = await api.get<AdminOrganizationSummary[]>('/admin/organizations', {
    params,
  });
  return response.data;
}

export async function getOrganization(orgId: string): Promise<AdminOrganizationDetail> {
  const response = await api.get<AdminOrganizationDetail>(`/admin/organizations/${orgId}`);
  return response.data;
}

export async function impersonateOrganization(orgId: string): Promise<AdminImpersonateResponse> {
  const response = await api.post<AdminImpersonateResponse>(
    `/admin/organizations/${orgId}/impersonate`
  );
  return response.data;
}

export async function updateOrganizationStatus(
  orgId: string,
  status: 'active' | 'suspended'
): Promise<AdminOrganizationSummary> {
  const response = await api.patch<AdminOrganizationSummary>(
    `/admin/organizations/${orgId}/status`,
    { status }
  );
  return response.data;
}

export async function listConversations(params?: {
  org_id?: string;
  skip?: number;
  limit?: number;
}): Promise<AdminConversationSummary[]> {
  const response = await api.get<AdminConversationSummary[]>('/admin/conversations', {
    params,
  });
  return response.data;
}

export async function getConversation(conversationId: string): Promise<AdminConversationDetail> {
  const response = await api.get<AdminConversationDetail>(
    `/admin/conversations/${conversationId}`
  );
  return response.data;
}

export async function getActivityFeed(limit?: number): Promise<AdminActivityItem[]> {
  const response = await api.get<AdminActivityItem[]>('/admin/activity', {
    params: { limit },
  });
  return response.data;
}

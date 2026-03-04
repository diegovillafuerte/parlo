'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import AdminLayout from '@/components/admin/AdminLayout';
import { listInsights, updateInsightStatus, getInsightStats } from '@/lib/api/admin';
import type { InsightSummary } from '@/lib/types';

const typeConfig: Record<string, { label: string; bg: string; text: string }> = {
  bug: { label: 'Bug', bg: 'bg-red-100', text: 'text-red-800' },
  feature_request: { label: 'Feature Request', bg: 'bg-purple-100', text: 'text-purple-800' },
  follow_up: { label: 'Follow Up', bg: 'bg-yellow-100', text: 'text-yellow-800' },
};

const severityConfig: Record<string, { label: string; bg: string; text: string }> = {
  critical: { label: 'Critical', bg: 'bg-red-100', text: 'text-red-800' },
  high: { label: 'High', bg: 'bg-orange-100', text: 'text-orange-800' },
  medium: { label: 'Medium', bg: 'bg-yellow-100', text: 'text-yellow-800' },
  low: { label: 'Low', bg: 'bg-gray-100', text: 'text-gray-800' },
};

const statusConfig: Record<string, { label: string; bg: string; text: string }> = {
  open: { label: 'Open', bg: 'bg-blue-100', text: 'text-blue-800' },
  acknowledged: { label: 'Acknowledged', bg: 'bg-yellow-100', text: 'text-yellow-800' },
  resolved: { label: 'Resolved', bg: 'bg-green-100', text: 'text-green-800' },
};

function qualityScoreColor(score: number): string {
  if (score >= 7) return 'text-green-600';
  if (score >= 4) return 'text-yellow-600';
  return 'text-red-600';
}

function InsightsContent() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [typeFilter, setTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const { data: stats } = useQuery({
    queryKey: ['admin-insight-stats'],
    queryFn: getInsightStats,
  });

  const { data: insights, isLoading, error } = useQuery({
    queryKey: ['admin-insights', typeFilter, statusFilter, severityFilter],
    queryFn: () => listInsights({
      insight_type: typeFilter || undefined,
      status: statusFilter || undefined,
      severity: severityFilter || undefined,
    }),
  });

  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: 'open' | 'acknowledged' | 'resolved' }) =>
      updateInsightStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-insights'] });
      queryClient.invalidateQueries({ queryKey: ['admin-insight-stats'] });
    },
  });

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('es-MX', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getNextAction = (insight: InsightSummary): { label: string; status: 'acknowledged' | 'resolved' } | null => {
    if (insight.status === 'open') return { label: 'Acknowledge', status: 'acknowledged' };
    if (insight.status === 'acknowledged') return { label: 'Resolve', status: 'resolved' };
    return null;
  };

  return (
    <AdminLayout>
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-gray-900">Insights</h2>

        {/* Stats Bar */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white shadow rounded-lg p-4">
              <div className="text-sm text-gray-500">Open</div>
              <div className="text-2xl font-bold text-blue-600">{stats.open}</div>
            </div>
            <div className="bg-white shadow rounded-lg p-4">
              <div className="text-sm text-gray-500">Bugs</div>
              <div className="text-2xl font-bold text-red-600">{stats.by_type?.bug || 0}</div>
            </div>
            <div className="bg-white shadow rounded-lg p-4">
              <div className="text-sm text-gray-500">Feature Requests</div>
              <div className="text-2xl font-bold text-purple-600">{stats.by_type?.feature_request || 0}</div>
            </div>
            <div className="bg-white shadow rounded-lg p-4">
              <div className="text-sm text-gray-500">Avg Quality</div>
              <div className={`text-2xl font-bold ${stats.avg_quality_score ? qualityScoreColor(stats.avg_quality_score) : 'text-gray-400'}`}>
                {stats.avg_quality_score ?? '-'}
              </div>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="flex gap-4">
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500"
          >
            <option value="">All Types</option>
            <option value="bug">Bug</option>
            <option value="feature_request">Feature Request</option>
            <option value="follow_up">Follow Up</option>
          </select>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500"
          >
            <option value="">All Statuses</option>
            <option value="open">Open</option>
            <option value="acknowledged">Acknowledged</option>
            <option value="resolved">Resolved</option>
          </select>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-500"
          >
            <option value="">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>

        {/* Insights Table */}
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="w-8 h-8 border-4 border-gray-600 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : error ? (
          <div className="bg-red-50 text-red-600 p-4 rounded-lg">
            Error loading insights
          </div>
        ) : insights && insights.length > 0 ? (
          <div className="bg-white shadow rounded-lg overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Title
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Severity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Quality
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Organization
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {insights.map((insight) => {
                  const type = typeConfig[insight.insight_type] || typeConfig.bug;
                  const severity = severityConfig[insight.severity] || severityConfig.medium;
                  const insightStatus = statusConfig[insight.status] || statusConfig.open;
                  const nextAction = getNextAction(insight);
                  const isExpanded = expandedId === insight.id;

                  return (
                    <tr key={insight.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${type.bg} ${type.text}`}>
                          {type.label}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <button
                          onClick={() => setExpandedId(isExpanded ? null : insight.id)}
                          className="text-left"
                        >
                          <div className="text-sm font-medium text-gray-900">{insight.title}</div>
                          {isExpanded && (
                            <div className="mt-2 space-y-2">
                              <p className="text-sm text-gray-600">{insight.description}</p>
                              <p className="text-xs text-gray-400 italic">{insight.conversation_summary}</p>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  router.push(`/admin/conversations/${insight.conversation_id}`);
                                }}
                                className="text-xs text-blue-600 hover:text-blue-900"
                              >
                                View Conversation
                              </button>
                            </div>
                          )}
                        </button>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${severity.bg} ${severity.text}`}>
                          {severity.label}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`text-sm font-bold ${qualityScoreColor(insight.quality_score)}`}>
                          {insight.quality_score}/10
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {insight.organization_name || 'Unknown'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(insight.created_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${insightStatus.bg} ${insightStatus.text}`}>
                          {insightStatus.label}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        {nextAction && (
                          <button
                            onClick={() => statusMutation.mutate({ id: insight.id, status: nextAction.status })}
                            disabled={statusMutation.isPending}
                            className="text-blue-600 hover:text-blue-900 disabled:opacity-50"
                          >
                            {nextAction.label}
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="bg-white shadow rounded-lg p-8 text-center text-gray-500">
            No insights found
          </div>
        )}
      </div>
    </AdminLayout>
  );
}

export default function AdminInsightsPage() {
  return <InsightsContent />;
}

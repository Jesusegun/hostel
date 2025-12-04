import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Card from '../components/common/Card.jsx'
import KpiCard from '../components/dashboard/KpiCard.jsx'
import TrendKpiCard from '../components/dashboard/TrendKpiCard.jsx'
import StatusBadge from '../components/dashboard/StatusBadge.jsx'
import TimeSeriesChart from '../components/dashboard/TimeSeriesChart.jsx'
import HallPerformanceTable from '../components/dashboard/HallPerformanceTable.jsx'
import DateRangeSelector from '../components/dashboard/DateRangeSelector.jsx'
import StatusDonutChart from '../components/dashboard/StatusDonutChart.jsx'
import ResolutionTimeChart from '../components/dashboard/ResolutionTimeChart.jsx'
import CategoryByHallChart from '../components/dashboard/CategoryByHallChart.jsx'
import Button from '../components/common/Button.jsx'
import { fetchIssueStats, fetchIssues } from '../services/issueService.js'
import { fetchAdminDashboardSummary } from '../services/dashboardService.js'
import { useAuth } from '../hooks/useAuth.js'

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Tooltip,
  Legend,
} from 'chart.js'
import { Bar, Pie, Doughnut } from 'react-chartjs-2'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, ArcElement, Tooltip, Legend)

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { position: 'top' },
  },
  scales: {
    y: {
      grid: { color: '#E5E7EB' },
      ticks: { color: '#6B7280' },
      beginAtZero: true,
    },
    x: {
      grid: { display: false },
      ticks: { color: '#6B7280' },
    },
  },
}

export default function DashboardPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [stats, setStats] = useState(null)
  const [adminSummary, setAdminSummary] = useState(null)
  const [recentIssues, setRecentIssues] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [dateRange, setDateRange] = useState(null)
  const isAdmin = user?.role === 'admin'

  const loadDashboardData = async (dateRangeParams = null) => {
    setLoading(true)
    setError(null)
    try {
      if (isAdmin) {
        // Use Promise.allSettled to handle partial failures gracefully
        const [summaryResult, issuesResult] = await Promise.allSettled([
          fetchAdminDashboardSummary(dateRangeParams || {}),
          fetchIssues({ page: 1, page_size: 5, status: 'all' }),
        ])
        
        // Handle summary data (can be partial)
        if (summaryResult.status === 'fulfilled') {
          setAdminSummary(summaryResult.value)
        } else {
          console.error('Failed to load dashboard summary:', summaryResult.reason)
          // Set empty summary structure to prevent crashes
          setAdminSummary({
            kpis: [],
            issues_by_category: [],
            issues_by_hall: [],
            issues_over_time: [],
            issues_by_status: [],
            resolution_time_by_hall: [],
            category_by_hall_stacked: [],
          })
          setError('Some dashboard data could not be loaded. Showing available information.')
        }
        
        // Handle recent issues (optional, don't fail if this fails)
        if (issuesResult.status === 'fulfilled') {
          setRecentIssues(issuesResult.value.issues || [])
        } else {
          console.error('Failed to load recent issues:', issuesResult.reason)
          setRecentIssues([])
        }
      } else {
        // Use Promise.allSettled for hall admin too
        const [statsResult, issuesResult] = await Promise.allSettled([
          fetchIssueStats(),
          fetchIssues({ page: 1, page_size: 5, status: 'all' }),
        ])
        
        // Handle stats data
        if (statsResult.status === 'fulfilled') {
          setStats(statsResult.value)
        } else {
          console.error('Failed to load issue stats:', statsResult.reason)
          // Set default stats to prevent crashes
          setStats({
            total: 0,
            pending: 0,
            in_progress: 0,
            done: 0,
            by_category: [],
            by_hall: null,
          })
          setError('Some dashboard data could not be loaded. Showing available information.')
        }
        
        // Handle recent issues
        if (issuesResult.status === 'fulfilled') {
          setRecentIssues(issuesResult.value.issues || [])
        } else {
          console.error('Failed to load recent issues:', issuesResult.reason)
          setRecentIssues([])
        }
      }
    } catch (err) {
      console.error('Dashboard load error:', err)
      // Only show error if we have no data at all
      if (!adminSummary && !stats) {
        setError('Failed to load dashboard data. Please try again.')
      } else {
        // We have partial data, just show a warning
        setError('Some dashboard data could not be loaded. Showing available information.')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDashboardData()
  }, [isAdmin])

  const handleDateRangeChange = (range) => {
    setDateRange(range)
    loadDashboardData(range)
  }

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="text-neutral-500">Loading dashboard...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-96 flex-col items-center justify-center">
        <p className="text-red-600">{error}</p>
        <Button onClick={() => window.location.reload()} className="mt-4">
          Retry
        </Button>
      </div>
    )
  }

  if (!isAdmin && !stats) return null
  if (isAdmin && !adminSummary) return null

  if (isAdmin) {
    const categoryChartData = {
      labels: adminSummary.issues_by_category?.map((c) => c.category_name) || [],
      datasets: [
        {
          data: adminSummary.issues_by_category?.map((c) => c.count) || [],
          backgroundColor: ['#2563EB', '#0EA5E9', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#F43F5E'],
        },
      ],
    }
    
    const categoryChartOptions = {
      ...chartOptions,
      maintainAspectRatio: true,
      plugins: {
        ...chartOptions.plugins,
        onClick: (event, elements) => {
          if (elements.length > 0) {
            const index = elements[0].index
            const categoryName = adminSummary.issues_by_category[index]?.category_name
            if (categoryName) {
              navigate(`/issues?category=${encodeURIComponent(categoryName)}`)
            }
          }
        },
      },
    }

    const sortedHalls = [...(adminSummary.issues_by_hall || [])].sort((a, b) => b.total - a.total)
    const hallChartSource = sortedHalls.slice(0, 8)
    const hallChartData =
      hallChartSource.length > 0
        ? {
            labels: hallChartSource.map((h) => h.hall_name),
            datasets: [
              {
                label: 'Issues',
                data: hallChartSource.map((h) => h.total),
                backgroundColor: '#2563EB',
              },
            ],
          }
        : null

    const topHalls = [...(adminSummary.issues_by_hall || [])]
      .sort((a, b) => b.total - a.total)
      .slice(0, 5)

    return (
      <div className="space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-neutral-900">Executive Overview</h2>
            <p className="mt-1 text-sm text-neutral-500">
              At-a-glance operational metrics • <span className="text-primary-600 cursor-pointer hover:underline" onClick={() => navigate('/analytics')}>View detailed analytics →</span>
            </p>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-6">
          {adminSummary.kpis?.map((kpi) => (
            <TrendKpiCard
              key={kpi.label}
              label={kpi.label}
              value={kpi.value}
              change={kpi.change}
              trend={kpi.trend}
              description={kpi.description}
            />
          ))}
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <div className="mb-6">
              <p className="text-sm font-semibold text-neutral-500">Issues by Status</p>
              <h3 className="text-2xl font-bold text-neutral-900">Current Workload</h3>
              <p className="text-xs text-neutral-500 mt-1">Click any segment to filter issues</p>
            </div>
            <StatusDonutChart data={adminSummary.issues_by_status || []} />
          </Card>

          <Card>
            <div className="mb-6">
              <p className="text-sm font-semibold text-neutral-500">Issues by Category</p>
              <h3 className="text-2xl font-bold text-neutral-900">Distribution</h3>
              <p className="text-xs text-neutral-500 mt-1">Click any segment to filter issues</p>
            </div>
            <div className="flex items-center justify-center" style={{ height: '300px' }}>
              {categoryChartData.labels.length ? (
                <Pie data={categoryChartData} options={categoryChartOptions} />
              ) : (
                <p className="text-neutral-500">No category data yet.</p>
              )}
            </div>
          </Card>
        </div>

        <Card>
          <div className="mb-6 flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-neutral-500">Hall Performance</p>
              <h3 className="text-2xl font-bold text-neutral-900">Top 5 Halls by Volume</h3>
              <p className="text-xs text-neutral-500 mt-1">Halls with the most issues</p>
            </div>
            <Button variant="ghost" className="text-sm" onClick={() => navigate('/analytics')}>
              View all halls →
            </Button>
          </div>
          {topHalls.length > 0 ? (
            <div className="mt-6 overflow-x-auto">
              <table className="w-full">
                <thead className="border-b border-neutral-200 bg-neutral-50 text-left text-xs font-semibold uppercase tracking-wider text-neutral-600">
                  <tr>
                    <th className="rounded-tl-xl px-4 py-3">Hall</th>
                    <th className="px-4 py-3 text-center">Total</th>
                    <th className="px-4 py-3 text-center">Pending</th>
                    <th className="px-4 py-3 text-center">In Progress</th>
                    <th className="px-4 py-3 text-center">Done</th>
                    <th className="rounded-tr-xl px-4 py-3 text-center">Completion %</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-100">
                  {topHalls.map((hall) => {
                    const completionRate = hall.total > 0 ? Math.round((hall.done / hall.total) * 100) : 0
                    return (
                      <tr
                        key={hall.hall_name}
                        className="cursor-pointer transition-colors hover:bg-neutral-50"
                        onClick={() => navigate(`/issues?hall=${encodeURIComponent(hall.hall_name)}`)}
                      >
                        <td className="px-4 py-4 text-sm font-semibold text-neutral-900">{hall.hall_name}</td>
                        <td className="px-4 py-4 text-center text-sm font-medium text-neutral-900">{hall.total}</td>
                        <td className="px-4 py-4 text-center text-sm text-status-pending">{hall.pending}</td>
                        <td className="px-4 py-4 text-center text-sm text-status-in-progress">{hall.in_progress}</td>
                        <td className="px-4 py-4 text-center text-sm text-status-done">{hall.done}</td>
                        <td className="px-4 py-4 text-center text-sm">
                          <span
                            className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${
                              completionRate >= 75
                                ? 'bg-status-done-bg text-status-done'
                                : completionRate >= 50
                                  ? 'bg-status-in-progress-bg text-status-in-progress'
                                  : 'bg-status-pending-bg text-status-pending'
                            }`}
                          >
                            {completionRate}%
                          </span>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="mt-6 text-center text-neutral-500">No hall data yet.</p>
          )}
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-neutral-500">Recent Issues</p>
              <h3 className="text-2xl font-bold text-neutral-900">Latest Reports</h3>
            </div>
            <Button variant="ghost" className="text-sm" onClick={() => navigate('/issues')}>
              View all →
            </Button>
          </div>
          {recentIssues.length === 0 ? (
            <p className="mt-6 text-center text-neutral-500">No issues yet.</p>
          ) : (
            <div className="mt-6 overflow-x-auto">
              <table className="w-full">
                <thead className="border-b border-neutral-200 bg-neutral-50 text-left text-xs font-semibold uppercase tracking-wider text-neutral-600">
                  <tr>
                    <th className="rounded-tl-xl px-4 py-3">Room</th>
                    <th className="px-4 py-3">Hall</th>
                    <th className="px-4 py-3">Category</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="rounded-tr-xl px-4 py-3">Created</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-100">
                  {recentIssues.map((issue) => (
                    <tr
                      key={issue.id}
                      className="cursor-pointer transition-colors hover:bg-neutral-50"
                      onClick={() => navigate(`/issues/${issue.id}`)}
                    >
                      <td className="px-4 py-4 text-sm font-medium text-neutral-900">{issue.room_number}</td>
                      <td className="px-4 py-4 text-sm text-neutral-600">{issue.hall_name}</td>
                      <td className="px-4 py-4 text-sm text-neutral-600">{issue.category_name}</td>
                      <td className="px-4 py-4">
                        <StatusBadge status={issue.status} />
                      </td>
                      <td className="px-4 py-4 text-sm text-neutral-500">
                        {new Date(issue.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      </div>
    )
  }

  const categoryChartData = {
    labels: stats.by_category?.map((c) => c.category_name) || [],
    datasets: [
      {
        data: stats.by_category?.map((c) => c.count) || [],
        backgroundColor: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'],
      },
    ],
  }

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-neutral-900">
          {user.role === 'admin' ? 'System Overview' : `${user.hall_name || 'Hall'} Dashboard`}
        </h2>
        <p className="mt-1 text-sm text-neutral-500">Real-time metrics and issue tracking</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KpiCard label="Total Issues" value={stats.total.toString()} change={`${stats.pending} pending`} />
        <KpiCard label="Pending" value={stats.pending.toString()} change="Awaiting action" />
        <KpiCard label="In Progress" value={stats.in_progress.toString()} change="Being worked on" />
        <KpiCard label="Resolved" value={stats.done.toString()} change="Completed" trend="up" />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <div className="mb-6">
            <p className="text-sm font-semibold text-neutral-500">Issues by Category</p>
            <h3 className="text-2xl font-bold text-neutral-900">Distribution</h3>
          </div>
          <div className="flex items-center justify-center" style={{ height: '300px' }}>
            <Pie data={categoryChartData} options={{ ...chartOptions, maintainAspectRatio: true }} />
          </div>
        </Card>
      </div>

      <Card>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold text-neutral-500">Recent Issues</p>
            <h3 className="text-2xl font-bold text-neutral-900">Latest Reports</h3>
          </div>
          <Button variant="ghost" className="text-sm" onClick={() => (window.location.href = '/issues')}>
            View all
          </Button>
        </div>
        {recentIssues.length === 0 ? (
          <p className="mt-6 text-center text-neutral-500">No issues yet.</p>
        ) : (
          <div className="mt-6 overflow-x-auto">
            <table className="w-full">
              <thead className="border-b border-neutral-200 bg-neutral-50 text-left text-xs font-semibold uppercase tracking-wider text-neutral-600">
                <tr>
                  <th className="rounded-tl-xl px-4 py-3">Room</th>
                  <th className="px-4 py-3">Hall</th>
                  <th className="px-4 py-3">Category</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="rounded-tr-xl px-4 py-3">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100">
                {recentIssues.map((issue) => (
                  <tr
                    key={issue.id}
                    className="cursor-pointer transition-colors hover:bg-neutral-50"
                    onClick={() => (window.location.href = `/issues/${issue.id}`)}
                  >
                    <td className="px-4 py-4 text-sm font-medium text-neutral-900">{issue.room_number}</td>
                    <td className="px-4 py-4 text-sm text-neutral-600">{issue.hall_name}</td>
                    <td className="px-4 py-4 text-sm text-neutral-600">{issue.category_name}</td>
                    <td className="px-4 py-4">
                      <StatusBadge status={issue.status} />
                    </td>
                    <td className="px-4 py-4 text-sm text-neutral-500">
                      {new Date(issue.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}


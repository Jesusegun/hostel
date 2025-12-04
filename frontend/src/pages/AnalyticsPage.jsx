import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Card from '../components/common/Card.jsx'
import TimeSeriesChart from '../components/dashboard/TimeSeriesChart.jsx'
import ResolutionTimeChart from '../components/dashboard/ResolutionTimeChart.jsx'
import CategoryByHallChart from '../components/dashboard/CategoryByHallChart.jsx'
import HallPerformanceTable from '../components/dashboard/HallPerformanceTable.jsx'
import DateRangeSelector from '../components/dashboard/DateRangeSelector.jsx'
import Button from '../components/common/Button.jsx'
import { fetchAdminDashboardSummary } from '../services/dashboardService.js'
import { useAuth } from '../hooks/useAuth.js'

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
  Legend,
} from 'chart.js'
import { Bar } from 'react-chartjs-2'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend)

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
  },
  scales: {
    y: {
      beginAtZero: true,
      grid: { color: '#E5E7EB' },
      ticks: { color: '#6B7280' },
    },
    x: {
      grid: { display: false },
      ticks: { color: '#6B7280' },
    },
  },
}

export default function AnalyticsPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [adminSummary, setAdminSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [dateRange, setDateRange] = useState(null)

  const loadAnalyticsData = async (dateRangeParams = null) => {
    setLoading(true)
    setError(null)
    try {
      const summaryData = await fetchAdminDashboardSummary(dateRangeParams || {})
      setAdminSummary(summaryData)
    } catch (err) {
      console.error('Analytics load error:', err)
      setError('Failed to load analytics data. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAnalyticsData()
  }, [])

  const handleDateRangeChange = (range) => {
    setDateRange(range)
    const params = {}
    if (range?.from) params.date_from = range.from
    if (range?.to) params.date_to = range.to
    loadAnalyticsData(params)
  }

  const handleHallClick = (hallName) => {
    navigate(`/issues?hall=${encodeURIComponent(hallName)}`)
  }

  if (loading && !adminSummary) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="text-neutral-500">Loading analytics...</div>
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

  if (!adminSummary) return null

  const sortedHalls = [...(adminSummary.issues_by_hall || [])].sort((a, b) => b.total - a.total)
  const hallChartData =
    sortedHalls.length > 0
      ? {
          labels: sortedHalls.map((h) => h.hall_name),
          datasets: [
            {
              label: 'Total Issues',
              data: sortedHalls.map((h) => h.total),
              backgroundColor: '#2563EB',
            },
          ],
        }
      : null

  const hallChartOptions = {
    ...chartOptions,
    onClick: (event, elements) => {
      if (elements.length > 0) {
        const index = elements[0].index
        const hallName = sortedHalls[index]?.hall_name
        if (hallName) {
          handleHallClick(hallName)
        }
      }
    },
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold text-neutral-500">Deep-Dive Analysis</p>
          <h2 className="text-3xl font-bold text-neutral-900">Analytics & Insights</h2>
          <p className="mt-1 text-sm text-neutral-500">
            Trend analysis, performance metrics, and strategic insights
          </p>
        </div>
        <DateRangeSelector onChange={handleDateRangeChange} defaultValue="30d" />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <div className="mb-6">
            <p className="text-sm font-semibold text-neutral-500">Issues Over Time</p>
            <h3 className="text-2xl font-bold text-neutral-900">Last 6 Months</h3>
            <p className="text-xs text-neutral-500 mt-1">Track issue submission trends</p>
          </div>
          <TimeSeriesChart data={adminSummary.issues_over_time} />
        </Card>

        <Card>
          <div className="mb-6">
            <p className="text-sm font-semibold text-neutral-500">Resolution Time by Hall</p>
            <h3 className="text-2xl font-bold text-neutral-900">Performance Metrics</h3>
            <p className="text-xs text-neutral-500 mt-1">Average days to resolve issues</p>
          </div>
          <ResolutionTimeChart data={adminSummary.resolution_time_by_hall || []} />
        </Card>
      </div>

      <Card>
        <div className="mb-6">
          <p className="text-sm font-semibold text-neutral-500">Hall Comparison</p>
          <h3 className="text-2xl font-bold text-neutral-900">Total Issues by Hall</h3>
          <p className="text-xs text-neutral-500 mt-1">Click any bar to view issues for that hall</p>
        </div>
        <div className="h-96">
          {hallChartData ? (
            <Bar data={hallChartData} options={hallChartOptions} />
          ) : (
            <p className="text-center text-neutral-500 py-8">No hall data yet.</p>
          )}
        </div>
      </Card>

      <Card>
        <div className="mb-6">
          <p className="text-sm font-semibold text-neutral-500">Issues by Category per Hall</p>
          <h3 className="text-2xl font-bold text-neutral-900">Stacked Breakdown</h3>
          <p className="text-xs text-neutral-500 mt-1">Category distribution across all halls</p>
        </div>
        <CategoryByHallChart data={adminSummary.category_by_hall_stacked || []} />
      </Card>

      <Card>
        <div className="mb-6">
          <p className="text-sm font-semibold text-neutral-500">Hall Performance</p>
          <h3 className="text-2xl font-bold text-neutral-900">Detailed Metrics (All Halls)</h3>
          <p className="text-xs text-neutral-500 mt-1">Comprehensive performance breakdown</p>
        </div>
        <HallPerformanceTable data={adminSummary.issues_by_hall || []} />
      </Card>
    </div>
  )
}

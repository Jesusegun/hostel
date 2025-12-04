import { Doughnut } from 'react-chartjs-2'
import { useNavigate } from 'react-router-dom'

/**
 * StatusDonutChart Component
 *
 * Displays issues breakdown by status (pending, in_progress, done) as a donut chart.
 * Supports drill-down on click to filter issues by status.
 *
 * @param {Object} props
 * @param {Array} props.data - Array of {status, count, percentage} objects
 * @param {boolean} props.enableDrillDown - Whether to enable click-to-filter (default: true)
 */
export default function StatusDonutChart({ data, enableDrillDown = true }) {
  const navigate = useNavigate()

  if (!data || data.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center text-neutral-500">
        No status data available
      </div>
    )
  }

  const statusColors = {
    pending: '#EF4444',
    in_progress: '#F59E0B',
    done: '#10B981',
  }

  const statusLabels = {
    pending: 'Pending',
    in_progress: 'In Progress',
    done: 'Done',
  }

  const chartData = {
    labels: data.map((item) => `${statusLabels[item.status] || item.status} (${item.percentage}%)`),
    datasets: [
      {
        data: data.map((item) => item.count),
        backgroundColor: data.map((item) => statusColors[item.status] || '#6B7280'),
        borderWidth: 2,
        borderColor: '#FFFFFF',
      },
    ],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          padding: 15,
          font: {
            size: 12,
          },
        },
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const label = context.label || ''
            const value = context.parsed || 0
            const total = context.dataset.data.reduce((a, b) => a + b, 0)
            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0
            return `${label}: ${value} (${percentage}%)`
          },
        },
      },
      ...(enableDrillDown && {
        onClick: (event, elements) => {
          if (elements.length > 0) {
            const index = elements[0].index
            const status = data[index].status
            navigate(`/issues?status=${status}`)
          }
        },
      }),
    },
  }

  return (
    <div className="flex items-center justify-center" style={{ height: '300px' }}>
      <Doughnut data={chartData} options={options} />
    </div>
  )
}


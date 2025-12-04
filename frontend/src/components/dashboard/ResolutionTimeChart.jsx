import { Bar } from 'react-chartjs-2'
import { useNavigate } from 'react-router-dom'

/**
 * ResolutionTimeChart Component
 *
 * Displays average resolution time (in days) per hall as a bar chart.
 * Color-codes bars by performance (green < 7 days, yellow 7-14, red > 14).
 * Supports drill-down on click to filter issues by hall.
 *
 * @param {Object} props
 * @param {Array} props.data - Array of {hall_name, avg_days} objects
 * @param {boolean} props.enableDrillDown - Whether to enable click-to-filter (default: true)
 */
export default function ResolutionTimeChart({ data, enableDrillDown = true }) {
  const navigate = useNavigate()

  if (!data || data.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center text-neutral-500">
        No resolution time data available
      </div>
    )
  }

  // Sort by avg_days descending (slowest first)
  const sortedData = [...data].sort((a, b) => b.avg_days - a.avg_days)

  // Color-code by performance
  const getColor = (days) => {
    if (days < 7) return '#10B981' // Green
    if (days < 14) return '#F59E0B' // Yellow
    return '#EF4444' // Red
  }

  const chartData = {
    labels: sortedData.map((item) => item.hall_name),
    datasets: [
      {
        label: 'Average Days to Resolve',
        data: sortedData.map((item) => item.avg_days),
        backgroundColor: sortedData.map((item) => getColor(item.avg_days)),
        borderColor: sortedData.map((item) => getColor(item.avg_days)),
        borderWidth: 1,
      },
    ],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const days = context.parsed.y.toFixed(1)
            return `Avg. Resolution: ${days} days`
          },
        },
      },
      ...(enableDrillDown && {
        onClick: (event, elements) => {
          if (elements.length > 0) {
            const index = elements[0].index
            const hallName = sortedData[index].hall_name
            navigate(`/issues?hall=${encodeURIComponent(hallName)}`)
          }
        },
      }),
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: 'Days',
        },
        grid: {
          color: '#E5E7EB',
        },
        ticks: {
          color: '#6B7280',
        },
      },
      x: {
        grid: {
          display: false,
        },
        ticks: {
          color: '#6B7280',
        },
      },
    },
  }

  return (
    <div className="h-80">
      <Bar data={chartData} options={options} />
    </div>
  )
}


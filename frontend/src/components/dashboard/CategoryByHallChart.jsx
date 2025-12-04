import { Bar } from 'react-chartjs-2'
import { useNavigate } from 'react-router-dom'

/**
 * CategoryByHallChart Component
 *
 * Displays issues by category per hall as a stacked bar chart.
 * X-axis: Hall names, Y-axis: Issue counts, Stacks: Categories.
 * Supports drill-down on click to filter issues by hall or category.
 *
 * @param {Object} props
 * @param {Array} props.data - Array of {hall_name, categories: [{category_name, count}]} objects
 * @param {boolean} props.enableDrillDown - Whether to enable click-to-filter (default: true)
 */
export default function CategoryByHallChart({ data, enableDrillDown = true }) {
  const navigate = useNavigate()

  if (!data || data.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center text-neutral-500">
        No category by hall data available
      </div>
    )
  }

  // Get all unique categories across all halls
  const allCategories = new Set()
  data.forEach((hall) => {
    hall.categories.forEach((cat) => allCategories.add(cat.category_name))
  })
  const categoryList = Array.from(allCategories)

  // Generate colors for categories
  const categoryColors = [
    '#2563EB', '#0EA5E9', '#10B981', '#F59E0B', '#EF4444',
    '#8B5CF6', '#EC4899', '#F43F5E', '#14B8A6', '#06B6D4',
  ]
  const colorMap = {}
  categoryList.forEach((cat, idx) => {
    colorMap[cat] = categoryColors[idx % categoryColors.length]
  })

  // Build datasets for each category
  const datasets = categoryList.map((categoryName) => ({
    label: categoryName,
    data: data.map((hall) => {
      const catData = hall.categories.find((c) => c.category_name === categoryName)
      return catData ? catData.count : 0
    }),
    backgroundColor: colorMap[categoryName],
  }))

  const chartData = {
    labels: data.map((item) => item.hall_name),
    datasets,
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          padding: 10,
          font: {
            size: 11,
          },
          boxWidth: 12,
        },
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const label = context.dataset.label || ''
            const value = context.parsed.y || 0
            return `${label}: ${value}`
          },
        },
      },
      ...(enableDrillDown && {
        onClick: (event, elements) => {
          if (elements.length > 0) {
            const element = elements[0]
            const hallName = data[element.index].hall_name
            navigate(`/issues?hall=${encodeURIComponent(hallName)}`)
          }
        },
      }),
    },
    scales: {
      x: {
        stacked: true,
        grid: {
          display: false,
        },
        ticks: {
          color: '#6B7280',
        },
      },
      y: {
        stacked: true,
        beginAtZero: true,
        title: {
          display: true,
          text: 'Number of Issues',
        },
        grid: {
          color: '#E5E7EB',
        },
        ticks: {
          color: '#6B7280',
        },
      },
    },
  }

  return (
    <div className="h-96">
      <Bar data={chartData} options={options} />
    </div>
  )
}


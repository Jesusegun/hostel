import PropTypes from 'prop-types'
import { Line } from 'react-chartjs-2'

const lineOptions = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index', intersect: false },
  stacked: false,
  plugins: {
    legend: { position: 'top' },
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

export default function TimeSeriesChart({ data }) {
  const labels = data?.map((point) => point.period) ?? []
  const chartData = {
    labels,
    datasets: [
      {
        label: 'Total',
        data: data?.map((point) => point.total) ?? [],
        borderColor: '#2563EB',
        backgroundColor: 'rgba(37, 99, 235, 0.1)',
        tension: 0.3,
        fill: true,
      },
      {
        label: 'Pending',
        data: data?.map((point) => point.pending) ?? [],
        borderColor: '#EF4444',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        tension: 0.3,
      },
      {
        label: 'In Progress',
        data: data?.map((point) => point.in_progress) ?? [],
        borderColor: '#F59E0B',
        backgroundColor: 'rgba(245, 158, 11, 0.1)',
        tension: 0.3,
      },
      {
        label: 'Done',
        data: data?.map((point) => point.done) ?? [],
        borderColor: '#10B981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        tension: 0.3,
      },
    ],
  }

  return <div style={{ height: '320px' }}>{labels.length ? <Line data={chartData} options={lineOptions} /> : null}</div>
}

TimeSeriesChart.propTypes = {
  data: PropTypes.arrayOf(
    PropTypes.shape({
      period: PropTypes.string.isRequired,
      total: PropTypes.number.isRequired,
      pending: PropTypes.number.isRequired,
      in_progress: PropTypes.number.isRequired,
      done: PropTypes.number.isRequired,
    }),
  ),
}

TimeSeriesChart.defaultProps = {
  data: [],
}



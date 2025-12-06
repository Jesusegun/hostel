import clsx from 'classnames'
import PropTypes from 'prop-types'

const trendStyles = {
  up: 'text-green-600',
  down: 'text-red-600',
  flat: 'text-neutral-500',
}

export default function HallPerformanceTable({ data = [] }) {
  if (!data || data.length === 0) {
    return <p className="mt-6 text-center text-neutral-500">No hall performance data yet.</p>
  }

  return (
    <div className="mt-6 overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="border-b border-neutral-200 bg-neutral-50 text-xs font-semibold uppercase tracking-wider text-neutral-600">
          <tr>
            <th className="px-4 py-3">Hall</th>
            <th className="px-4 py-3">Total</th>
            <th className="px-4 py-3">Pending</th>
            <th className="px-4 py-3">In Progress</th>
            <th className="px-4 py-3">Done</th>
            <th className="px-4 py-3">% Done</th>
            <th className="px-4 py-3">Trend</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-neutral-100">
          {data.map((hall) => (
            <tr key={hall.hall_name} className="hover:bg-neutral-50">
              <td className="px-4 py-3 font-medium text-neutral-900">{hall.hall_name}</td>
              <td className="px-4 py-3 text-neutral-700">{hall.total}</td>
              <td className="px-4 py-3 text-neutral-700">{hall.pending}</td>
              <td className="px-4 py-3 text-neutral-700">{hall.in_progress}</td>
              <td className="px-4 py-3 text-neutral-700">{hall.done}</td>
              <td className="px-4 py-3 text-neutral-700">{`${hall.completion_rate.toFixed(1)}%`}</td>
              <td className="px-4 py-3 font-semibold">
                <span className={clsx(trendStyles[hall.trend] || trendStyles.flat)}>
                  {hall.trend === 'up' && '↑'}
                  {hall.trend === 'down' && '↓'}
                  {hall.trend === 'flat' && '→'} {hall.change.toFixed(1)}%
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

HallPerformanceTable.propTypes = {
  data: PropTypes.arrayOf(
    PropTypes.shape({
      hall_name: PropTypes.string.isRequired,
      total: PropTypes.number.isRequired,
      pending: PropTypes.number.isRequired,
      in_progress: PropTypes.number.isRequired,
      done: PropTypes.number.isRequired,
      completion_rate: PropTypes.number.isRequired,
      change: PropTypes.number.isRequired,
      trend: PropTypes.oneOf(['up', 'down', 'flat']).isRequired,
    }),
  ),
}



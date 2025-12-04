import PropTypes from 'prop-types'
import Card from '../common/Card.jsx'

const trendColors = {
  up: 'text-green-600',
  down: 'text-status-pending',
  flat: 'text-neutral-500',
}

export default function KpiCard({ label, value, change, trend = 'flat' }) {
  return (
    <Card className="space-y-2">
      <p className="text-sm text-neutral-500">{label}</p>
      <p className="text-3xl font-semibold text-neutral-900">{value}</p>
      {change && <p className={`text-sm font-medium ${trendColors[trend]}`}>{change}</p>}
    </Card>
  )
}

KpiCard.propTypes = {
  label: PropTypes.string.isRequired,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
  change: PropTypes.string,
  trend: PropTypes.oneOf(['up', 'down', 'flat']),
}

KpiCard.defaultProps = {
  change: null,
  trend: 'flat',
}


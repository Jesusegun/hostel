import clsx from 'classnames'
import PropTypes from 'prop-types'
import Card from '../common/Card.jsx'

const trendStyles = {
  up: 'text-green-600 bg-green-50',
  down: 'text-red-600 bg-red-50',
  flat: 'text-neutral-500 bg-neutral-100',
}

const trendIcons = {
  up: '↑',
  down: '↓',
  flat: '→',
}

export default function TrendKpiCard({ label, value, change, trend, description }) {
  const formattedChange =
    typeof change === 'number' ? `${change > 0 ? '+' : change < 0 ? '' : ''}${change.toFixed(1)}%` : change

  const getTrendColor = () => {
    if (trend === 'up') return 'text-green-600'
    if (trend === 'down') return 'text-red-600'
    return 'text-neutral-500'
  }

  return (
    <Card className="space-y-2">
      <p className="text-sm text-neutral-500">{label}</p>
      <p className="text-3xl font-semibold text-neutral-900">{value}</p>
      {change !== null && change !== undefined && (
        <p className={clsx('text-sm font-semibold flex items-center gap-1', getTrendColor())}>
          <span aria-hidden>{trendIcons[trend] || trendIcons.flat}</span>
          {formattedChange}
        </p>
      )}
      {description && <p className="text-xs text-neutral-500 mt-1">{description}</p>}
    </Card>
  )
}

TrendKpiCard.propTypes = {
  label: PropTypes.string.isRequired,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
  change: PropTypes.number,
  trend: PropTypes.oneOf(['up', 'down', 'flat']),
  description: PropTypes.string,
}

TrendKpiCard.defaultProps = {
  change: null,
  trend: 'flat',
  description: null,
}



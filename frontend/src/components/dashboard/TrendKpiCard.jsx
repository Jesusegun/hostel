import clsx from 'classnames'
import PropTypes from 'prop-types'
import Card from '../common/Card.jsx'

const trendIcons = {
  up: '↑',
  down: '↓',
  flat: '→',
}

export default function TrendKpiCard({ label, value, change = null, trend = 'flat', description = null, lowerIsBetter = false }) {
  const formattedChange =
    typeof change === 'number' ? `${change > 0 ? '+' : ''}${change.toFixed(1)}%` : change

  /**
   * Get trend color based on direction and lowerIsBetter flag.
   * 
   * For metrics where lower is better (resolution time, pending, issues this month):
   *   - Down trend = GREEN (improvement)
   *   - Up trend = RED (getting worse)
   * 
   * For metrics where higher is better (resolved count) or neutral:
   *   - Up trend = GREEN (improvement)
   *   - Down trend = RED (getting worse)
   */
  const getTrendColor = () => {
    if (trend === 'flat') return 'text-neutral-500'
    
    if (lowerIsBetter) {
      // Lower is better: down = good (green), up = bad (red)
      return trend === 'down' ? 'text-green-600' : 'text-red-600'
    } else {
      // Higher is better or neutral: up = good (green), down = bad (red)
      return trend === 'up' ? 'text-green-600' : 'text-red-600'
    }
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
  lowerIsBetter: PropTypes.bool,
}
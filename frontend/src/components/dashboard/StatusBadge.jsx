import PropTypes from 'prop-types'
import clsx from 'classnames'

const styles = {
  pending: 'bg-status-pending-bg text-status-pending',
  'in_progress': 'bg-status-progress-bg text-status-progress',
  done: 'bg-status-done-bg text-status-done',
}

export default function StatusBadge({ status }) {
  return (
    <span
      className={clsx(
        'rounded-full px-3 py-1 text-xs font-semibold capitalize',
        styles[status] || 'bg-neutral-100 text-neutral-700',
      )}
    >
      {status.replace('_', ' ')}
    </span>
  )
}

StatusBadge.propTypes = {
  status: PropTypes.string.isRequired,
}


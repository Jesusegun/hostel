import clsx from 'classnames'
import PropTypes from 'prop-types'

export default function Card({ children, className, onClick }) {
  return (
    <div className={clsx('rounded-2xl bg-white p-6 shadow-card', className)} onClick={onClick}>
      {children}
    </div>
  )
}

Card.propTypes = {
  children: PropTypes.node.isRequired,
  className: PropTypes.string,
  onClick: PropTypes.func,
}

Card.defaultProps = {
  className: '',
  onClick: undefined,
}


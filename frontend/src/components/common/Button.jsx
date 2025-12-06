import clsx from 'classnames'
import PropTypes from 'prop-types'

export default function Button({ children, variant = 'primary', className = '', ...props }) {
  const baseClasses =
    'inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-semibold transition-all duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 active:scale-95'
  const variants = {
    primary: 'bg-primary-600 text-white hover:bg-primary-700 active:bg-primary-800 focus-visible:outline-primary-600',
    secondary: 'bg-white text-primary-600 border border-primary-100 hover:bg-primary-50 active:bg-primary-100 focus-visible:outline-primary-600',
    danger: 'bg-status-pending text-white hover:bg-red-600 active:bg-red-700 focus-visible:outline-red-600',
    ghost: 'bg-transparent text-gray-600 hover:text-gray-900 active:bg-gray-100',
  }

  return (
    <button className={clsx(baseClasses, variants[variant], className)} {...props}>
      {children}
    </button>
  )
}

Button.propTypes = {
  children: PropTypes.node.isRequired,
  variant: PropTypes.oneOf(['primary', 'secondary', 'danger', 'ghost']),
  className: PropTypes.string,
}


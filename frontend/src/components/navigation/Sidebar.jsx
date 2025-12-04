import PropTypes from 'prop-types'
import { NavLink } from 'react-router-dom'
import clsx from 'classnames'
import { useState } from 'react'
import useAuth from '../../hooks/useAuth.js'
import { formatUsername } from '../../utils/formatUsername.js'

const mainLinks = [
  { label: 'Dashboard', to: '/dashboard' },
  { label: 'Issues', to: '/hall-selection', roles: ['admin'] },
  { label: 'Issues', to: '/issues', roles: ['hall_admin'] },
  { label: 'Analytics', to: '/analytics', roles: ['admin'] },
]

const managementLinks = [
  { label: 'Users', to: '/admin/users' },
  { label: 'Halls', to: '/admin/halls' },
  { label: 'Categories', to: '/admin/categories' },
]

export default function Sidebar({ isOpen, onClose }) {
  const { user } = useAuth()
  const [isManagementExpanded, setIsManagementExpanded] = useState(false)

  const toggleManagement = () => {
    setIsManagementExpanded(!isManagementExpanded)
  }

  return (
    <>
      <div
        className={clsx(
          'fixed inset-0 z-30 bg-gray-900/60 transition-opacity lg:hidden',
          isOpen ? 'opacity-100' : 'pointer-events-none opacity-0',
        )}
        onClick={onClose}
      />
      <aside
        className={clsx(
          'fixed inset-y-0 left-0 z-40 w-72 transform bg-neutral-900 text-white shadow-xl transition-transform lg:translate-x-0',
          isOpen ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        <div className="flex h-full flex-col">
          <div className="px-6 py-6">
            <p className="text-sm uppercase tracking-widest text-neutral-300">Hostel Maintenance</p>
            <p className="text-2xl font-semibold text-white">Caleb University</p>
          </div>
          <div className="px-6 pb-4">
            <div className="rounded-xl bg-neutral-800 px-4 py-3">
              <p className="text-sm text-neutral-400">Signed in as</p>
              <p className="text-lg font-semibold text-white">{formatUsername(user?.username)}</p>
              <p className="text-sm text-neutral-400">{user?.role === 'admin' ? 'Admin User' : 'Hall Admin'}</p>
            </div>
          </div>
          <nav className="flex-1 space-y-1 px-4">
            {mainLinks
              .filter((link) => !link.roles || link.roles.includes(user?.role))
              .map((link) => (
                <NavLink
                  key={link.to}
                  to={link.to}
                  className={({ isActive }) =>
                    clsx(
                      'flex items-center rounded-xl px-4 py-3 text-sm font-semibold transition-colors',
                      isActive ? 'bg-primary-600 text-white' : 'text-neutral-300 hover:bg-neutral-800',
                    )
                  }
                  onClick={onClose}
                >
                  {link.label}
                </NavLink>
              ))}
            
            {/* Management section - only for DSA */}
            {user?.username === 'dsa' && (
              <div className="mt-6">
                <button
                  onClick={toggleManagement}
                  className={clsx(
                    'flex w-full items-center justify-between rounded-xl px-4 py-3 text-sm font-semibold transition-colors',
                    'text-neutral-300 hover:bg-neutral-800',
                  )}
                >
                  <span>Management</span>
                  <svg
                    className={clsx(
                      'h-5 w-5 transition-transform',
                      isManagementExpanded ? 'rotate-180' : '',
                    )}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                </button>
                {isManagementExpanded && (
                  <div className="ml-4 space-y-1 border-l-2 border-neutral-700 pl-2">
                    {managementLinks.map((link) => (
                      <NavLink
                        key={link.to}
                        to={link.to}
                        className={({ isActive }) =>
                          clsx(
                            'flex items-center rounded-xl px-4 py-3 text-sm font-semibold transition-colors',
                            isActive ? 'bg-primary-600 text-white' : 'text-neutral-300 hover:bg-neutral-800',
                          )
                        }
                        onClick={onClose}
                      >
                        {link.label}
                      </NavLink>
                    ))}
                  </div>
                )}
              </div>
            )}
          </nav>
        </div>
      </aside>
    </>
  )
}

Sidebar.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
}


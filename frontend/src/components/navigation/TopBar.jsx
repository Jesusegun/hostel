import PropTypes from 'prop-types'
import Button from '../common/Button.jsx'
import useAuth from '../../hooks/useAuth.js'
import { formatUsername } from '../../utils/formatUsername.js'

export default function TopBar({ onMenuClick }) {
  const { user, logout } = useAuth()

  return (
    <header className="sticky top-0 z-20 flex items-center justify-between border-b border-neutral-100 bg-white/90 px-4 py-4 backdrop-blur lg:px-8">
      <div className="flex items-center gap-3">
        <button
          type="button"
          className="rounded-xl border border-neutral-200 p-2 text-neutral-700 lg:hidden"
          onClick={onMenuClick}
        >
          <span className="sr-only">Open navigation</span>
          ☰
        </button>
        <div>
          <p className="text-xs uppercase text-neutral-500">Hostel Repairs</p>
          <p className="text-lg font-semibold text-neutral-900">Operations Overview</p>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <div className="hidden md:block">
          <div className="relative">
            <input
              type="search"
              placeholder="Search room, hall, category"
              className="w-72 rounded-xl border border-neutral-200 bg-neutral-50 px-4 py-2 text-sm focus:border-primary-500 focus:outline-none"
            />
            <span className="pointer-events-none absolute inset-y-0 right-4 flex items-center text-neutral-400">⌕</span>
          </div>
        </div>
        <div className="text-right">
          <p className="text-sm font-semibold text-neutral-900">{formatUsername(user?.username)}</p>
          <p className="text-xs uppercase tracking-wide text-neutral-500">{user?.role || 'unauthenticated'}</p>
        </div>
        <Button variant="secondary" onClick={logout}>
          Logout
        </Button>
      </div>
    </header>
  )
}

TopBar.propTypes = {
  onMenuClick: PropTypes.func.isRequired,
}


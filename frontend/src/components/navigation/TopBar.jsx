import PropTypes from 'prop-types'
import { useEffect, useRef, useState } from 'react'
import Button from '../common/Button.jsx'
import useAuth from '../../hooks/useAuth.js'
import { formatUsername } from '../../utils/formatUsername.js'
import ChangePasswordModal from './ChangePasswordModal.jsx'

export default function TopBar({ onMenuClick }) {
  const { user, logout } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)
  const [showChangePassword, setShowChangePassword] = useState(false)
  const menuRef = useRef(null)

  useEffect(() => {
    if (!menuOpen) return undefined

    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setMenuOpen(false)
      }
    }

    const handleEscape = (event) => {
      if (event.key === 'Escape') {
        setMenuOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    window.addEventListener('keydown', handleEscape)

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
      window.removeEventListener('keydown', handleEscape)
    }
  }, [menuOpen])

  const openChangePassword = () => {
    setMenuOpen(false)
    setShowChangePassword(true)
  }

  const handleLogout = async () => {
    setMenuOpen(false)
    await logout()
  }

  return (
    <>
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
            <p className="text-xs uppercase text-neutral-500">Hostel Maintenance</p>
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
          <div className="relative" ref={menuRef}>
            <button
              type="button"
              className="rounded-lg px-2 py-1 text-right transition-colors hover:bg-neutral-100"
              onClick={() => setMenuOpen((previous) => !previous)}
              aria-haspopup="menu"
              aria-expanded={menuOpen}
            >
              <p className="text-sm font-semibold text-neutral-900">
                {formatUsername(user?.username)} <span className="text-neutral-500">▾</span>
              </p>
              <p className="text-xs uppercase tracking-wide text-neutral-500">{user?.role || 'unauthenticated'}</p>
            </button>

            {menuOpen && (
              <div
                className="absolute right-0 mt-2 w-48 rounded-xl border border-neutral-200 bg-white p-1 shadow-lg"
                role="menu"
              >
                <button
                  type="button"
                  className="w-full rounded-lg px-3 py-2 text-left text-sm font-medium text-neutral-700 hover:bg-neutral-100"
                  onClick={openChangePassword}
                  role="menuitem"
                >
                  Change Password
                </button>
                <div className="my-1 border-t border-neutral-100" />
                <button
                  type="button"
                  className="w-full rounded-lg px-3 py-2 text-left text-sm font-medium text-neutral-700 hover:bg-neutral-100"
                  onClick={handleLogout}
                  role="menuitem"
                >
                  Logout
                </button>
              </div>
            )}
          </div>
          <Button variant="secondary" onClick={logout}>
            Logout
          </Button>
        </div>
      </header>

      <ChangePasswordModal open={showChangePassword} onClose={() => setShowChangePassword(false)} />
    </>
  )
}

TopBar.propTypes = {
  onMenuClick: PropTypes.func.isRequired,
}


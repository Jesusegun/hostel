import PropTypes from 'prop-types'
import { useEffect, useMemo, useState } from 'react'
import Button from '../common/Button.jsx'
import { changePassword } from '../../services/authService.js'

const initialForm = {
  current_password: '',
  new_password: '',
  confirm_password: '',
}

export default function ChangePasswordModal({ open, onClose }) {
  const [form, setForm] = useState(initialForm)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    if (!open) {
      setForm(initialForm)
      setError('')
      setSuccess('')
      setSubmitting(false)
    }
  }, [open])

  useEffect(() => {
    if (!open) return undefined

    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        onClose()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [open, onClose])

  const canSubmit = useMemo(() => {
    return (
      form.current_password.trim().length > 0
      && form.new_password.length >= 8
      && form.confirm_password.length >= 8
      && !submitting
    )
  }, [form, submitting])

  const handleChange = (field) => (event) => {
    setForm((previous) => ({ ...previous, [field]: event.target.value }))
    setError('')
    setSuccess('')
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setSuccess('')

    if (form.new_password !== form.confirm_password) {
      setError('New password and confirmation do not match.')
      return
    }

    if (form.current_password === form.new_password) {
      setError('New password must be different from current password.')
      return
    }

    try {
      setSubmitting(true)
      await changePassword(form)
      setSuccess('Password updated successfully.')
      setForm(initialForm)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update password. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/35 px-4"
      onClick={onClose}
      role="presentation"
    >
      <div
        className="w-full max-w-md rounded-2xl border border-neutral-200 bg-white p-5 shadow-xl"
        onClick={(event) => event.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label="Change password"
      >
        <div className="mb-4">
          <h2 className="text-lg font-semibold text-neutral-900">Change Password</h2>
          <p className="mt-1 text-sm text-neutral-500">Use at least 8 characters.</p>
        </div>

        <form className="space-y-3" onSubmit={handleSubmit}>
          <div>
            <label htmlFor="current_password" className="mb-1 block text-sm font-medium text-neutral-700">
              Current password
            </label>
            <input
              id="current_password"
              type="password"
              value={form.current_password}
              onChange={handleChange('current_password')}
              className="w-full rounded-xl border border-neutral-200 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none"
              autoComplete="current-password"
              required
            />
          </div>

          <div>
            <label htmlFor="new_password" className="mb-1 block text-sm font-medium text-neutral-700">
              New password
            </label>
            <input
              id="new_password"
              type="password"
              value={form.new_password}
              onChange={handleChange('new_password')}
              className="w-full rounded-xl border border-neutral-200 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none"
              autoComplete="new-password"
              required
              minLength={8}
            />
          </div>

          <div>
            <label htmlFor="confirm_password" className="mb-1 block text-sm font-medium text-neutral-700">
              Confirm new password
            </label>
            <input
              id="confirm_password"
              type="password"
              value={form.confirm_password}
              onChange={handleChange('confirm_password')}
              className="w-full rounded-xl border border-neutral-200 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none"
              autoComplete="new-password"
              required
              minLength={8}
            />
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}
          {success && <p className="text-sm text-emerald-600">{success}</p>}

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="ghost" onClick={onClose}>
              Close
            </Button>
            <Button type="submit" disabled={!canSubmit}>
              {submitting ? 'Updating...' : 'Update Password'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

ChangePasswordModal.propTypes = {
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
}

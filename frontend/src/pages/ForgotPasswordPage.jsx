import { useState } from 'react'
import { Link } from 'react-router-dom'
import Card from '../components/common/Card.jsx'
import Button from '../components/common/Button.jsx'
import { requestPasswordReset } from '../services/authService.js'

export default function ForgotPasswordPage() {
  const [identifier, setIdentifier] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      setLoading(true)
      setError('')
      setSuccess('')

      await requestPasswordReset(identifier.trim())
      setSuccess('If an account exists for that username/email, a reset link has been sent.')
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to submit reset request. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-50 px-4 py-12">
      <Card className="w-full max-w-md">
        <h2 className="text-2xl font-bold text-neutral-900">Forgot Password</h2>
        <p className="mt-2 text-sm text-neutral-600">
          Enter your username or email. If a matching account exists, we will send a reset link.
        </p>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          {error && (
            <div className="rounded-lg bg-red-50 p-3 text-sm text-red-600">
              {error}
            </div>
          )}

          {success && (
            <div className="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700">
              {success}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-neutral-700">
              Username or Email
            </label>
            <input
              type="text"
              required
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              className="mt-1 w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              placeholder="Enter your username or email"
            />
          </div>

          <div className="rounded-lg bg-blue-50 p-3 text-sm text-blue-800">
            If you cannot access your email, please contact DSA for account recovery support.
          </div>

          <div className="flex gap-3 pt-4">
            <Link to="/login" className="flex-1">
              <Button variant="ghost" className="w-full" type="button">
                Back to Login
              </Button>
            </Link>
            <Button type="submit" className="flex-1" disabled={loading}>
              {loading ? 'Sending...' : 'Send Reset Link'}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  )
}


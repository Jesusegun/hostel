import { useState } from 'react'
import { Navigate, useLocation, Link } from 'react-router-dom'
import Button from '../components/common/Button.jsx'
import useAuth from '../hooks/useAuth.js'

export default function LoginPage() {
  const { login, isAuthenticated, loading } = useAuth()
  const location = useLocation()
  const redirectTo = location.state?.from?.pathname || '/dashboard'
  const [formState, setFormState] = useState({ username: '', password: '' })
  const [error, setError] = useState(null)

  if (isAuthenticated) {
    return <Navigate to={redirectTo} replace />
  }

  const handleChange = (event) => {
    const { name, value } = event.target
    setFormState((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError(null)
    try {
      await login(formState)
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to sign in. Please check your credentials.')
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-600 via-primary-500 to-primary-400 flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md">
        {/* Logo/Title Section */}
        <div className="text-center mb-8">
          <h1 className="text-2xl md:text-3xl font-bold text-white mb-2">CALEB UNIVERSITY</h1>
          <p className="text-base md:text-lg text-primary-100 font-medium">Maintenance Portal</p>
        </div>

        {/* Login Card */}
        <div className="bg-white rounded-2xl shadow-2xl p-8 md:p-10">
          <div className="mb-8">
            <p className="text-sm font-semibold uppercase tracking-wider text-primary-600 mb-2">
              Welcome Back
            </p>
            <h2 className="text-2xl font-bold text-neutral-900">Sign in to continue</h2>
            <p className="mt-2 text-sm text-neutral-600">
              Use the username and password shared with you.
            </p>
          </div>

          <form className="space-y-5" onSubmit={handleSubmit}>
            {/* Username Field */}
            <div>
              <label className="block text-sm font-semibold text-neutral-700 mb-2" htmlFor="username">
                Username
              </label>
              <input
                id="username"
                name="username"
                type="text"
                required
                value={formState.username}
                onChange={handleChange}
                className="block w-full px-4 py-3 border border-neutral-200 rounded-xl text-sm placeholder-neutral-400 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors outline-none"
                placeholder="Enter your username"
              />
            </div>

            {/* Password Field */}
            <div>
              <label className="block text-sm font-semibold text-neutral-700 mb-2" htmlFor="password">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                value={formState.password}
                onChange={handleChange}
                className="block w-full px-4 py-3 border border-neutral-200 rounded-xl text-sm placeholder-neutral-400 focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors outline-none"
                placeholder="Enter your password"
              />
            </div>

            {/* Error Message */}
            {error && (
              <div className={`rounded-xl border px-4 py-3 ${
                error.includes('locked') 
                  ? 'bg-amber-50 border-amber-200' 
                  : 'bg-red-50 border-red-200'
              }`}>
                <p className={`text-sm font-medium ${
                  error.includes('locked') ? 'text-amber-800' : 'text-red-800'
                }`}>
                  {error.includes('locked') ? '🔒 ' : ''}{error}
                </p>
              </div>
            )}

            {/* Submit Button */}
            <Button className="w-full mt-6" type="submit" disabled={loading}>
              {loading ? 'Signing in…' : 'Sign in'}
            </Button>
          </form>

          {/* Forgot Password Link */}
          <div className="mt-6 text-center">
            <Link
              to="/forgot-password"
              className="text-sm text-primary-600 hover:text-primary-700 font-medium transition-colors"
            >
              Forgot Password?
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}


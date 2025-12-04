import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import Card from '../components/common/Card.jsx'
import Button from '../components/common/Button.jsx'
import { getSecurityQuestion, verifySecurityAnswer } from '../services/adminService.js'

export default function ForgotPasswordPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState(1) // 1: username, 2: question + answer (DSA only), 3: success, 4: contact DSA, 5: DSA needs to set question
  const [username, setUsername] = useState('')
  const [question, setQuestion] = useState(null)
  const [answer, setAnswer] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleGetQuestion = async (e) => {
    e.preventDefault()
    try {
      setLoading(true)
      setError(null)
      
      const response = await getSecurityQuestion(username.trim())
      const trimmedUsername = username.trim().toLowerCase()
      
      if (response.question) {
        // User has security question (DSA only) - show security question workflow
        setQuestion(response.question)
        setStep(2)
      } else if (trimmedUsername === 'dsa') {
        // DSA user but no security question set - show message to set it first
        setStep(5)
      } else {
        // Other users don't have security question - show contact DSA message
        setStep(4)
      }
    } catch (err) {
      console.error('Failed to get security question:', err)
      // If user not found, still show contact DSA message
      if (err.response?.status === 404) {
        setStep(4)
      } else {
        setError(err.response?.data?.detail || 'Failed to retrieve security question. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleResetPassword = async (e) => {
    e.preventDefault()
    
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match')
      return
    }
    
    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters long')
      return
    }
    
    try {
      setLoading(true)
      setError(null)
      
      await verifySecurityAnswer({
        username: username.trim(),
        answer: answer.trim(),
        new_password: newPassword,
      })
      
      setStep(3)
    } catch (err) {
      console.error('Failed to reset password:', err)
      setError(err.response?.data?.detail || 'Failed to reset password. Please check your answer and try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-50 px-4 py-12">
      <Card className="w-full max-w-md">
        {step === 1 && (
          <>
            <h2 className="text-2xl font-bold text-neutral-900">Forgot Password</h2>
            <p className="mt-2 text-sm text-neutral-600">
              Enter your username to continue.
            </p>
            
            <form onSubmit={handleGetQuestion} className="mt-6 space-y-4">
              {error && (
                <div className="rounded-lg bg-red-50 p-3 text-sm text-red-600">
                  {error}
                </div>
              )}
              
              <div>
                <label className="block text-sm font-medium text-neutral-700">
                  Username
                </label>
                <input
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                  placeholder="Enter your username"
                />
              </div>
              
              <div className="flex gap-3 pt-4">
                <Link to="/login" className="flex-1">
                  <Button variant="ghost" className="w-full" type="button">
                    Back to Login
                  </Button>
                </Link>
                <Button type="submit" className="flex-1" disabled={loading}>
                  {loading ? 'Loading...' : 'Continue'}
                </Button>
              </div>
            </form>
          </>
        )}

        {step === 2 && (
          <>
            <h2 className="text-2xl font-bold text-neutral-900">Answer Security Question</h2>
            <p className="mt-2 text-sm text-neutral-600">
              Answer your security question and set a new password.
            </p>
            
            <form onSubmit={handleResetPassword} className="mt-6 space-y-4">
              {error && (
                <div className="rounded-lg bg-red-50 p-3 text-sm text-red-600">
                  {error}
                </div>
              )}
              
              <div className="rounded-lg bg-neutral-50 p-4">
                <p className="text-sm font-medium text-neutral-700">Security Question:</p>
                <p className="mt-1 text-sm text-neutral-900">{question}</p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-neutral-700">
                  Answer
                </label>
                <input
                  type="text"
                  required
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                  placeholder="Enter your answer"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-neutral-700">
                  New Password
                </label>
                <input
                  type="password"
                  required
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                  placeholder="Minimum 8 characters"
                  minLength={8}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-neutral-700">
                  Confirm Password
                </label>
                <input
                  type="password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                  placeholder="Confirm your password"
                  minLength={8}
                />
              </div>
              
              <div className="flex gap-3 pt-4">
                <Button
                  type="button"
                  variant="ghost"
                  className="flex-1"
                  onClick={() => {
                    setStep(1)
                    setAnswer('')
                    setNewPassword('')
                    setConfirmPassword('')
                    setError(null)
                  }}
                >
                  Back
                </Button>
                <Button type="submit" className="flex-1" disabled={loading}>
                  {loading ? 'Resetting...' : 'Reset Password'}
                </Button>
              </div>
            </form>
          </>
        )}

        {step === 3 && (
          <>
            <div className="text-center">
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-green-100">
                <svg
                  className="h-6 w-6 text-green-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-neutral-900">Password Reset Successful</h2>
              <p className="mt-2 text-sm text-neutral-600">
                Your password has been reset. Please login with your new password.
              </p>
              
              <div className="mt-6">
                <Link to="/login">
                  <Button className="w-full">Go to Login</Button>
                </Link>
              </div>
            </div>
          </>
        )}

        {step === 4 && (
          <>
            <div className="text-center">
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-blue-100">
                <svg
                  className="h-6 w-6 text-blue-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-neutral-900">Contact DSA for Password Reset</h2>
              <p className="mt-4 text-sm text-neutral-600">
                Please contact the DSA (Dean of Student Affairs) to reset your password.
              </p>
              
              <div className="mt-6 space-y-3">
                <Link to="/login">
                  <Button variant="ghost" className="w-full">
                    Back to Login
                  </Button>
                </Link>
              </div>
            </div>
          </>
        )}

        {step === 5 && (
          <>
            <div className="text-center">
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-yellow-100">
                <svg
                  className="h-6 w-6 text-yellow-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-neutral-900">Security Question Not Set</h2>
              <p className="mt-4 text-sm text-neutral-600">
                You need to set your security question before you can use password recovery.
              </p>
              <p className="mt-2 text-sm text-neutral-600">
                Please log in and set your security question in your account settings.
              </p>
              
              <div className="mt-6 space-y-3">
                <Link to="/login">
                  <Button className="w-full">
                    Go to Login
                  </Button>
                </Link>
              </div>
            </div>
          </>
        )}
      </Card>
    </div>
  )
}


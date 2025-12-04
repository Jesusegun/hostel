import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Card from '../components/common/Card.jsx'
import Button from '../components/common/Button.jsx'
import { setSecurityQuestion } from '../services/adminService.js'
import useAuth from '../hooks/useAuth.js'

export default function SetSecurityQuestionPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)

  // Only DSA can access this page
  useEffect(() => {
    if (user?.username !== 'dsa') {
      navigate('/dashboard')
    }
  }, [user, navigate])

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      setLoading(true)
      setError(null)
      
      await setSecurityQuestion({
        question: question.trim(),
        answer: answer.trim(),
      })
      
      setSuccess(true)
      setTimeout(() => {
        navigate('/dashboard')
      }, 2000)
    } catch (err) {
      console.error('Failed to set security question:', err)
      setError(err.response?.data?.detail || 'Failed to set security question. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  if (user?.username !== 'dsa') {
    return null
  }

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-neutral-900">Set Security Question</h2>
        <p className="mt-1 text-sm text-neutral-500">
          Set a security question for password recovery
        </p>
      </div>

      <Card className="max-w-2xl">
        {success ? (
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
            <h3 className="text-lg font-semibold text-neutral-900">Security Question Set</h3>
            <p className="mt-2 text-sm text-neutral-600">
              Your security question has been set successfully. Redirecting...
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="rounded-lg bg-red-50 p-3 text-sm text-red-600">
                {error}
              </div>
            )}
            
            <div>
              <label className="block text-sm font-medium text-neutral-700">
                Security Question *
              </label>
              <input
                type="text"
                required
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                className="mt-1 w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                placeholder="e.g., What city were you born in?"
                maxLength={500}
              />
              <p className="mt-1 text-xs text-neutral-500">
                Choose a question that only you know the answer to.
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-neutral-700">
                Answer *
              </label>
              <input
                type="text"
                required
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                className="mt-1 w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                placeholder="Enter your answer"
              />
              <p className="mt-1 text-xs text-neutral-500">
                Remember this answer - you'll need it to reset your password.
              </p>
            </div>
            
            <div className="flex gap-3 pt-4">
              <Button
                type="button"
                variant="ghost"
                onClick={() => navigate('/dashboard')}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={loading}>
                {loading ? 'Saving...' : 'Set Security Question'}
              </Button>
            </div>
          </form>
        )}
      </Card>
    </div>
  )
}


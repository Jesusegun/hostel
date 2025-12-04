import { useCallback, useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { format } from 'date-fns'
import Card from '../components/common/Card.jsx'
import Button from '../components/common/Button.jsx'
import StatusBadge from '../components/dashboard/StatusBadge.jsx'
import { fetchIssueById, updateIssueStatus } from '../services/issueService.js'
import { formatUsername } from '../utils/formatUsername.js'

const STATUS_SEQUENCE = ['pending', 'in_progress', 'done']

export default function IssueDetailPage() {
  const { issueId } = useParams()
  const [issue, setIssue] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [updating, setUpdating] = useState(false)
  const [message, setMessage] = useState(null)

  const loadIssue = useCallback(
    async ({ showLoading = true } = {}) => {
      if (showLoading) {
        setLoading(true)
      }
      setError(null)
      try {
        const data = await fetchIssueById(issueId)
        setIssue(data)
      } catch (err) {
        setError(err.response?.data?.detail || 'Unable to load issue.')
      } finally {
        if (showLoading) {
          setLoading(false)
        }
      }
    },
    [issueId],
  )

  useEffect(() => {
    loadIssue()
  }, [loadIssue])

  useEffect(() => {
    const interval = setInterval(() => {
      loadIssue({ showLoading: false })
    }, 60000)
    return () => clearInterval(interval)
  }, [loadIssue])

  const handleStatusChange = async (nextStatus) => {
    setUpdating(true)
    setMessage(null)
    try {
      const updated = await updateIssueStatus(issueId, nextStatus)
      setIssue(updated)
      setMessage(`Status updated to ${nextStatus.replace('_', ' ')}.`)
    } catch (err) {
      setMessage(err.response?.data?.detail || 'Failed to update status.')
    } finally {
      setUpdating(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-10 w-64 animate-pulse rounded bg-neutral-200" />
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="h-96 animate-pulse rounded-2xl bg-neutral-200 lg:col-span-2" />
          <div className="h-96 animate-pulse rounded-2xl bg-neutral-200" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-2xl border border-status-pending-bg bg-status-pending-bg px-6 py-5 text-status-pending">
        {error}{' '}
        <button type="button" className="font-semibold underline" onClick={loadIssue}>
          Try again
        </button>
      </div>
    )
  }

  if (!issue) {
    return null
  }

  const nextStatusIndex = Math.min(STATUS_SEQUENCE.indexOf(issue.status) + 1, STATUS_SEQUENCE.length - 1)
  const nextStatus = STATUS_SEQUENCE[nextStatusIndex]

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-neutral-500">Issue Details</p>
          <h2 className="text-3xl font-bold text-neutral-900">
            {issue.hall_name} • Room {issue.room_number}
          </h2>
          <p className="text-sm text-neutral-500">
            Submitted {issue.created_at ? format(new Date(issue.created_at), 'dd MMM yyyy HH:mm') : '—'}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <StatusBadge status={issue.status} />
          <Button variant="secondary" onClick={() => loadIssue()} disabled={loading}>
            Refresh
          </Button>
          {issue.status !== nextStatus && nextStatus !== 'done' && (
            <Button variant="secondary" onClick={() => handleStatusChange(nextStatus)} disabled={updating}>
              {updating ? (
                <span className="inline-flex items-center gap-2">
                  <svg
                    className="h-4 w-4 animate-spin"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Updating...
                </span>
              ) : (
                `Mark ${nextStatus.replace('_', ' ')}`
              )}
            </Button>
          )}
          {issue.status !== 'done' && (
            <Button onClick={() => handleStatusChange('done')} disabled={updating}>
              {updating ? (
                <span className="inline-flex items-center gap-2">
                  <svg
                    className="h-4 w-4 animate-spin"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Marking...
                </span>
              ) : (
                'Mark Done'
              )}
            </Button>
          )}
        </div>
      </div>

      {message && <p className="rounded-xl bg-neutral-100 px-4 py-3 text-sm text-neutral-700">{message}</p>}

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          {issue.image_url && (
            <img
              src={issue.image_url}
              alt="Issue"
              className="w-full rounded-2xl object-cover"
              loading="lazy"
              decoding="async"
            />
          )}
          <div className="mt-6 space-y-4">
            <div>
              <p className="text-xs uppercase text-neutral-500">Description</p>
              <p className="text-base text-neutral-800">{issue.description || 'No description provided.'}</p>
            </div>
            <div className="grid gap-6 sm:grid-cols-2">
              <div>
                <p className="text-xs uppercase text-neutral-500">Category</p>
                <p className="text-base font-semibold text-neutral-900">{issue.category_name}</p>
              </div>
              <div>
                <p className="text-xs uppercase text-neutral-500">Last Updated</p>
                <p className="text-base text-neutral-800">
                  {issue.updated_at ? format(new Date(issue.updated_at), 'dd MMM yyyy HH:mm') : '—'}
                </p>
              </div>
            </div>
          </div>
        </Card>

        <Card>
          <p className="text-sm font-semibold text-neutral-500">Student Contact</p>
          <h3 className="text-2xl font-bold text-neutral-900">{issue.student_name || 'Anonymous'}</h3>
          <p className="text-sm text-neutral-500">{issue.student_email}</p>
          <div className="mt-8 space-y-2 rounded-2xl bg-neutral-50 p-4 text-sm text-neutral-600">
            <p className="font-semibold text-neutral-900">Audit trail</p>
            {issue.audit_logs?.length === 0 && <p>No audit entries yet.</p>}
            {issue.audit_logs?.map((log) => (
              <p key={log.id}>
                • {format(new Date(log.timestamp), 'dd MMM HH:mm')} - {formatUsername(log.username || 'System')} changed{' '}
                {log.action} from {log.old_value || '—'} to {log.new_value || '—'}
              </p>
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}


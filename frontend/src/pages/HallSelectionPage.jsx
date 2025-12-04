import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { format, formatDistanceToNow, addMinutes } from 'date-fns'
import Card from '../components/common/Card.jsx'
import Button from '../components/common/Button.jsx'
import { fetchHallsWithStats } from '../services/hallService.js'
import { fetchIssueStats } from '../services/issueService.js'
import useAuth from '../hooks/useAuth.js'
import { fetchSyncStatus, triggerManualSync } from '../services/syncService.js'

export default function HallSelectionPage() {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [halls, setHalls] = useState([])
  const [systemStats, setSystemStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [syncStatus, setSyncStatus] = useState(null)
  const [syncing, setSyncing] = useState(false)

  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [hallsData, statsData] = await Promise.all([
        fetchHallsWithStats(),
        fetchIssueStats(),
      ])
      setHalls(hallsData)
      setSystemStats(statsData)
    } catch (err) {
      console.error('Failed to load halls:', err)
      setError('Failed to load hall data. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  const loadSyncStatus = useCallback(async () => {
    try {
      const data = await fetchSyncStatus()
      setSyncStatus(data)
      return true
    } catch (err) {
      console.error('Failed to load sync status:', err)
      return false
    }
  }, [])

  useEffect(() => {
    if (user?.role !== 'admin') {
      return undefined
    }
    let cancelled = false
    let timeoutId
    let delay = 30000

    const poll = async () => {
      const ok = await loadSyncStatus()
      delay = ok ? 30000 : Math.min(delay * 2, 120000)
      if (!cancelled) {
        timeoutId = setTimeout(poll, delay)
      }
    }

    poll()

    return () => {
      cancelled = true
      if (timeoutId) {
        clearTimeout(timeoutId)
      }
    }
  }, [loadSyncStatus, user?.role])

  const handleManualSync = async () => {
    setSyncing(true)
    try {
      await triggerManualSync()
      await Promise.all([loadSyncStatus(), loadData()])
    } catch (err) {
      console.error('Manual sync failed:', err)
      alert(err.response?.data?.detail || 'Failed to trigger sync. Please try again.')
    } finally {
      setSyncing(false)
    }
  }

  const formatSyncTime = (isoString) => {
    if (!isoString) return 'Never'
    const date = new Date(isoString)
    return format(date, 'h:mm a')
  }

  const getNextScheduledTime = () => {
    if (!syncStatus?.last_sync?.completed_at) return null
    const lastSync = new Date(syncStatus.last_sync.completed_at)
    return addMinutes(lastSync, 15)
  }

  const nextScheduled = getNextScheduledTime()
  const lastSync = syncStatus?.last_sync
  const lastFailed = syncStatus?.last_failed_sync

  const formatRelativeTime = (isoString) => {
    if (!isoString) return 'Never'
    return formatDistanceToNow(new Date(isoString), { addSuffix: true })
  }

  const handleHallClick = (hallName) => {
    navigate(`/issues?hall=${encodeURIComponent(hallName)}`)
  }

  const handleAllHallsClick = () => {
    navigate('/issues')
  }

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="text-neutral-500">Loading halls...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-96 flex-col items-center justify-center">
        <p className="text-red-600">{error}</p>
        <Button onClick={() => window.location.reload()} className="mt-4">
          Retry
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-neutral-500">Issue Management</p>
          <h2 className="text-3xl font-bold text-neutral-900">Select a Hall</h2>
          <p className="mt-1 text-sm text-neutral-500">
            Choose a hall to view and manage its issues, or view all halls combined
          </p>
        </div>
        <div className="flex gap-3">
          <Button variant="secondary" onClick={loadData}>
            Refresh
          </Button>
          {user?.role === 'admin' && (
            <Button onClick={handleManualSync} disabled={syncing}>
              {syncing ? 'Syncing...' : 'Trigger Manual Sync'}
            </Button>
          )}
        </div>
      </div>

      {user?.role === 'admin' && syncStatus && (
        <Card className="bg-gradient-to-r from-primary-50 to-blue-50 border-primary-200">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-sm font-semibold text-primary-700">Google Sheets Integration</p>
              <h3 className="text-lg font-bold text-primary-900">Sync Status</h3>
              <p className="text-sm text-primary-600">
                The APScheduler job pulls new submissions every 15 minutes.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-6">
              <div className="text-right">
                <p className="text-xs font-semibold text-primary-600 uppercase tracking-wide">Last Sync</p>
                {lastSync ? (
                  <>
                    <p className="text-xl font-bold text-primary-900">
                      {formatSyncTime(lastSync.completed_at || lastSync.started_at)}
                    </p>
                    <p
                      className={`text-xs font-semibold ${
                        lastSync.status === 'success' ? 'text-status-done' : 'text-status-pending'
                      }`}
                    >
                      {lastSync.status === 'success' ? 'Success' : 'Failed'} •{' '}
                      {lastSync.rows_processed || 0} rows processed
                    </p>
                  </>
                ) : (
                  <>
                    <p className="text-xl font-bold text-primary-900">Never</p>
                    <p className="text-xs text-primary-500">No syncs yet</p>
                  </>
                )}
              </div>
              {nextScheduled && (
                <div className="text-right">
                  <p className="text-xs font-semibold text-primary-600 uppercase tracking-wide">
                    Next Scheduled
                  </p>
                  <p className="text-xl font-bold text-primary-900">{format(nextScheduled, 'h:mm a')}</p>
                  <p className="text-xs text-primary-500">Runs every 15 minutes</p>
                </div>
              )}
            </div>
            {lastFailed && (
              <p className="mt-3 text-xs font-semibold text-status-pending">
                Last failure {formatRelativeTime(lastFailed.completed_at || lastFailed.started_at)}
              </p>
            )}
          </div>
        </Card>
      )}

      {/* All Halls Card */}
      <Card
        className="cursor-pointer border-2 border-primary-200 bg-gradient-to-br from-primary-50 to-blue-50 transition-all hover:shadow-lg hover:border-primary-400"
        onClick={handleAllHallsClick}
      >
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3">
              <h3 className="text-2xl font-bold text-primary-900">All Halls</h3>
              <span className="rounded-full bg-primary-600 px-3 py-1 text-sm font-semibold text-white">
                System-Wide
              </span>
            </div>
            <p className="mt-2 text-sm text-primary-700">View all issues across all halls</p>
          </div>
          {systemStats && (
            <div className="flex gap-8">
              <div className="text-center">
                <p className="text-3xl font-bold text-primary-900">{systemStats.total}</p>
                <p className="text-xs text-primary-600">Total Issues</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-status-pending">{systemStats.pending}</p>
                <p className="text-xs text-neutral-600">Pending</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-status-in-progress">{systemStats.in_progress}</p>
                <p className="text-xs text-neutral-600">In Progress</p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-status-done">{systemStats.done}</p>
                <p className="text-xs text-neutral-600">Done</p>
              </div>
            </div>
          )}
        </div>
      </Card>

      {/* Individual Hall Cards */}
      <div>
        <h3 className="mb-4 text-lg font-semibold text-neutral-700">Individual Halls</h3>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {halls.map((hall) => {
            const urgencyLevel =
              hall.pending_issues > 10 ? 'high' : hall.pending_issues > 5 ? 'medium' : 'low'
            const borderColor =
              urgencyLevel === 'high'
                ? 'border-red-300 hover:border-red-500'
                : urgencyLevel === 'medium'
                  ? 'border-yellow-300 hover:border-yellow-500'
                  : 'border-neutral-200 hover:border-primary-400'

            return (
              <Card
                key={hall.id}
                className={`cursor-pointer border-2 transition-all hover:shadow-lg ${borderColor}`}
                onClick={() => handleHallClick(hall.name)}
              >
                <div className="space-y-3">
                  <div className="flex items-start justify-between">
                    <h4 className="text-xl font-bold text-neutral-900">{hall.name}</h4>
                    {hall.total_issues > 0 && (
                      <span
                        className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
                          urgencyLevel === 'high'
                            ? 'bg-red-100 text-red-700'
                            : urgencyLevel === 'medium'
                              ? 'bg-yellow-100 text-yellow-700'
                              : 'bg-neutral-100 text-neutral-700'
                        }`}
                      >
                        {hall.total_issues} {hall.total_issues === 1 ? 'issue' : 'issues'}
                      </span>
                    )}
                  </div>

                  {hall.total_issues > 0 ? (
                    <>
                      <div className="flex justify-between text-sm">
                        <span className="text-neutral-600">Pending:</span>
                        <span className="font-semibold text-status-pending">{hall.pending_issues}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-neutral-600">In Progress:</span>
                        <span className="font-semibold text-status-in-progress">{hall.in_progress_issues}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-neutral-600">Done:</span>
                        <span className="font-semibold text-status-done">{hall.done_issues}</span>
                      </div>

                      {hall.last_issue_created_at && (
                        <div className="border-t border-neutral-100 pt-2">
                          <p className="text-xs text-neutral-500">
                            Last issue:{' '}
                            {formatDistanceToNow(new Date(hall.last_issue_created_at), { addSuffix: true })}
                          </p>
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="py-4 text-center">
                      <p className="text-sm text-neutral-500">No issues reported</p>
                      <p className="text-xs text-neutral-400 mt-1">All clear! ✓</p>
                    </div>
                  )}
                </div>
              </Card>
            )
          })}
        </div>
      </div>
    </div>
  )
}


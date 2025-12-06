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
      </div>

      {/* Compact Sync Status Bar - Admin Only */}
      {user?.role === 'admin' && syncStatus && (
        <div className="flex items-center justify-between rounded-lg bg-neutral-50 border border-neutral-200 px-4 py-2.5">
          <div className="flex items-center gap-3">
            {/* Status Indicator */}
            <span
              className={`h-2.5 w-2.5 rounded-full ${
                lastSync?.status === 'success'
                  ? 'bg-green-500'
                  : lastSync?.status === 'failed'
                    ? 'bg-red-500'
                    : 'bg-yellow-500'
              }`}
              title={lastSync?.status === 'success' ? 'Healthy' : 'Attention needed'}
            />
            <span className="text-sm text-neutral-700">
              {lastSync ? (
                <>
                  Synced {formatRelativeTime(lastSync.completed_at || lastSync.started_at)}
                  {lastSync.rows_processed > 0 && (
                    <span className="text-neutral-500"> • {lastSync.rows_processed} new</span>
                  )}
                </>
              ) : (
                'Never synced'
              )}
            </span>
            {nextScheduled && (
              <span className="text-sm text-neutral-500">
                • Next: {format(nextScheduled, 'h:mm a')}
              </span>
            )}
            {/* Show failure warning only if within 24 hours */}
            {lastFailed && new Date() - new Date(lastFailed.completed_at || lastFailed.started_at) < 24 * 60 * 60 * 1000 && (
              <span className="text-sm text-amber-600 font-medium">
                • Failed {formatRelativeTime(lastFailed.completed_at || lastFailed.started_at)}
              </span>
            )}
          </div>
          <Button
            variant="ghost"
            className="text-sm px-3 py-1.5"
            onClick={handleManualSync}
            disabled={syncing}
          >
            {syncing ? 'Syncing...' : 'Sync Now'}
          </Button>
        </div>
      )}

      {/* Hall Cards Grid */}
      <div>
        <h3 className="mb-4 text-lg font-semibold text-neutral-700">Select a Hall</h3>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {/* All Halls Card - First in Grid */}
          <Card
            className="cursor-pointer border-2 border-primary-300 bg-gradient-to-br from-primary-50 to-blue-50 transition-all hover:shadow-lg hover:border-primary-500"
            onClick={handleAllHallsClick}
          >
            <div className="space-y-3">
              <div className="flex items-start justify-between">
                <h4 className="text-xl font-bold text-primary-600">All Halls</h4>
                {systemStats && systemStats.total > 0 && (
                  <span className="rounded-full bg-primary-100 px-2.5 py-1 text-xs font-semibold text-primary-700">
                    {systemStats.total} {systemStats.total === 1 ? 'issue' : 'issues'}
                  </span>
                )}
              </div>

              {systemStats && systemStats.total > 0 ? (
                <>
                  <div className="flex justify-between text-sm">
                    <span className="text-neutral-600">Pending:</span>
                    <span className="font-semibold text-status-pending">{systemStats.pending}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-neutral-600">In Progress:</span>
                    <span className="font-semibold text-status-in-progress">{systemStats.in_progress}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-neutral-600">Done:</span>
                    <span className="font-semibold text-status-done">{systemStats.done}</span>
                  </div>

                  <div className="border-t border-primary-100 pt-2">
                    <p className="text-xs text-primary-600">System-wide view</p>
                  </div>
                </>
              ) : (
                <div className="py-4 text-center">
                  <p className="text-sm text-primary-600">No issues reported</p>
                  <p className="text-xs text-primary-400 mt-1">All clear! ✓</p>
                </div>
              )}
            </div>
          </Card>

          {/* Individual Hall Cards */}
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


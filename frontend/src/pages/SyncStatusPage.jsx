import { useState, useEffect, useCallback } from 'react'
import { format, formatDistanceToNow, addMinutes } from 'date-fns'
import Card from '../components/common/Card.jsx'
import Button from '../components/common/Button.jsx'
import { fetchSyncStatus, triggerManualSync } from '../services/syncService.js'

export default function SyncStatusPage() {
  const [syncData, setSyncData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [syncing, setSyncing] = useState(false)
  const [successMessage, setSuccessMessage] = useState(null)

  const loadSyncStatus = useCallback(
    async (showSpinner = false) => {
      if (showSpinner) {
        setLoading(true)
      }
      if (showSpinner) {
        setError(null)
      }
      try {
        const data = await fetchSyncStatus()
        setSyncData(data)
        if (!showSpinner) {
          setError(null)
        }
        return true
      } catch (err) {
        console.error('Failed to load sync status:', err)
        setError('Failed to load sync status. Please try again.')
        return false
      } finally {
        if (showSpinner) {
          setLoading(false)
        }
      }
    },
    [],
  )

  useEffect(() => {
    let cancelled = false
    let timeoutId

    const scheduleNext = (delay) => {
      if (cancelled) return
      timeoutId = setTimeout(async () => {
        const ok = await loadSyncStatus(false)
        const nextDelay = ok ? 30000 : 60000
        scheduleNext(nextDelay)
      }, delay)
    }

    const bootstrap = async () => {
      await loadSyncStatus(true)
      scheduleNext(30000)
    }

    bootstrap()

    return () => {
      cancelled = true
      if (timeoutId) {
        clearTimeout(timeoutId)
      }
    }
  }, [loadSyncStatus])

  const handleManualSync = async () => {
    setSyncing(true)
    setError(null)
    setSuccessMessage(null)
    
    // Store the sync start time to check if a new sync appears
    const syncStartTime = new Date()
    
    try {
      const result = await triggerManualSync()
      if (result?.retry_summary) {
        const { entries_checked, images_uploaded, errors } = result.retry_summary
        setSuccessMessage(
          `Manual sync completed. Retried ${entries_checked} pending images, ${images_uploaded} succeeded${
            errors && errors.length ? `. ${errors.length} errors logged.` : '.'
          }`,
        )
      } else {
        setSuccessMessage('Manual sync completed successfully.')
      }
      // Reload status after sync completes
      await loadSyncStatus(true)
    } catch (err) {
      console.error('Manual sync request failed:', err)
      
      // Check if it's a timeout error
      const isTimeout = err.code === 'ECONNABORTED' || err.message?.includes('timeout')
      
      if (isTimeout) {
        // Timeout occurred - sync might still be running
        // Poll sync status to check if it completed
        setError('Sync request timed out. Checking if sync completed...')
        
        // Poll for up to 30 seconds to see if sync completed
        let pollAttempts = 0
        const maxPollAttempts = 6 // 6 attempts * 5 seconds = 30 seconds
        const pollInterval = 5000 // 5 seconds
        
        const checkSyncCompletion = async () => {
          try {
            const statusData = await fetchSyncStatus()
            const lastSync = statusData?.last_sync
            
            // Check if there's a new sync that started after we triggered
            if (lastSync) {
              const lastSyncTime = new Date(lastSync.started_at)
              
              // If the last sync started after we triggered, it's our sync
              if (lastSyncTime >= syncStartTime) {
                if (lastSync.status === 'success') {
                  setError(null)
                  setSuccessMessage(
                    `Sync completed successfully! Processed ${lastSync.rows_processed} rows, created ${lastSync.rows_created} issues.`
                  )
                  await loadSyncStatus(true)
                  return true // Success, stop polling
                } else if (lastSync.status === 'failed') {
                  setError(`Sync failed: ${lastSync.errors?.[0] || 'Unknown error'}`)
                  await loadSyncStatus(true)
                  return true // Failed, stop polling
                }
                // Still in progress, continue polling
              }
            }
            
            pollAttempts++
            if (pollAttempts < maxPollAttempts) {
              // Continue polling
              setTimeout(checkSyncCompletion, pollInterval)
            } else {
              // Max attempts reached
              setError(
                'Sync request timed out and could not verify completion. ' +
                'Please check the sync status below to see if it completed.'
              )
              await loadSyncStatus(true)
            }
            return false
          } catch (pollErr) {
            console.error('Error polling sync status:', pollErr)
            setError(
              'Sync request timed out. Unable to verify if sync completed. ' +
              'Please check the sync status below.'
            )
            await loadSyncStatus(true)
            return false
          }
        }
        
        // Start polling after a short delay
        setTimeout(checkSyncCompletion, pollInterval)
      } else {
        // Other error (not timeout)
        setError(err.response?.data?.detail || 'Failed to trigger sync. Please try again.')
      }
    } finally {
      setSyncing(false)
    }
  }

  const formatSyncTime = (isoString) => {
    if (!isoString) return 'Never'
    const date = new Date(isoString)
    return format(date, 'h:mm a')
  }

  const formatSyncDate = (isoString) => {
    if (!isoString) return 'Never'
    const date = new Date(isoString)
    const now = new Date()
    const diffHours = (now - date) / (1000 * 60 * 60)

    if (diffHours < 24) {
      return `Today • ${format(date, 'h:mm a')}`
    } else if (diffHours < 48) {
      return `Yesterday • ${format(date, 'h:mm a')}`
    } else {
      return formatDistanceToNow(date, { addSuffix: true })
    }
  }

  const getNextScheduledTime = () => {
    if (!syncData?.last_sync?.completed_at) return null
    const lastSync = new Date(syncData.last_sync.completed_at)
    return addMinutes(lastSync, 15)
  }

  const countRecentErrors = () => {
    if (!syncData?.recent_syncs) return 0
    const last24h = new Date(Date.now() - 24 * 60 * 60 * 1000)
    return syncData.recent_syncs.filter((sync) => {
      if (sync.status !== 'failed') return false
      const syncTime = new Date(sync.completed_at || sync.started_at)
      return syncTime >= last24h
    }).length
  }

  if (loading && !syncData) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="text-neutral-500">Loading sync status...</div>
      </div>
    )
  }

  const lastSync = syncData?.last_sync
  const lastFailed = syncData?.last_failed_sync
  const nextScheduled = getNextScheduledTime()
  const errorCount = countRecentErrors()

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-neutral-500">Google Sheets Integration</p>
          <h2 className="text-3xl font-bold text-neutral-900">Sync Status</h2>
          <p className="text-sm text-neutral-500">The APScheduler job pulls new submissions every 15 minutes.</p>
        </div>
        <Button onClick={handleManualSync} disabled={syncing}>
          {syncing ? 'Syncing...' : 'Trigger Manual Sync'}
        </Button>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-800">
          {error}
        </div>
      )}
      {successMessage && (
        <div className="rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800">
          {successMessage}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        <Card>
          <p className="text-sm text-neutral-500">Last Sync</p>
          {lastSync ? (
            <>
              <p className="text-2xl font-bold text-neutral-900">{formatSyncTime(lastSync.completed_at || lastSync.started_at)}</p>
              <p
                className={`text-sm ${
                  lastSync.status === 'success' ? 'text-status-done' : 'text-status-pending'
                }`}
              >
                {lastSync.status === 'success' ? 'Success' : 'Failed'} • {lastSync.rows_processed} rows processed
              </p>
            </>
          ) : (
            <>
              <p className="text-2xl font-bold text-neutral-900">Never</p>
              <p className="text-sm text-neutral-500">No syncs yet</p>
            </>
          )}
        </Card>
        <Card>
          <p className="text-sm text-neutral-500">Next Scheduled</p>
          {nextScheduled ? (
            <>
              <p className="text-2xl font-bold text-neutral-900">{format(nextScheduled, 'h:mm a')}</p>
              <p className="text-sm text-neutral-500">Runs every 15 minutes</p>
            </>
          ) : (
            <>
              <p className="text-2xl font-bold text-neutral-900">N/A</p>
              <p className="text-sm text-neutral-500">Waiting for first sync</p>
            </>
          )}
        </Card>
        <Card>
          <p className="text-sm text-neutral-500">Last Failure</p>
          {lastFailed ? (
            <>
              <p className="text-2xl font-bold text-neutral-900">
                {formatSyncTime(lastFailed.completed_at || lastFailed.started_at)}
              </p>
              <p className="text-sm text-status-pending">
                {formatSyncDate(lastFailed.completed_at || lastFailed.started_at)}
              </p>
              <p className="text-xs text-neutral-500 mt-2">
                {errorCount} failures detected in the last 24 hours
              </p>
            </>
          ) : (
            <>
              <p className="text-2xl font-bold text-neutral-900">None</p>
              <p className="text-sm text-neutral-500">No failures recorded</p>
            </>
          )}
        </Card>
      </div>

      <Card>
        <p className="text-sm font-semibold text-neutral-500">Recent Logs</p>
        <div className="mt-4 space-y-3">
          {syncData?.recent_syncs && syncData.recent_syncs.length > 0 ? (
            syncData.recent_syncs.map((sync) => (
              <div
                key={sync.id}
                className="flex items-center justify-between rounded-2xl border border-neutral-100 px-4 py-3"
              >
                <div>
                  <p className="text-sm font-semibold text-neutral-900">
                    {formatSyncDate(sync.completed_at || sync.started_at)}
                  </p>
                  <p className="text-xs text-neutral-500">
                    {sync.rows_processed} rows processed • {sync.rows_created} created • {sync.rows_skipped} skipped
                    {sync.sync_type === 'manual' && ' • Manual'}
                  </p>
                </div>
                <span
                  className={`rounded-full px-3 py-1 text-xs font-semibold ${
                    sync.status === 'success'
                      ? 'bg-status-done-bg text-status-done'
                      : 'bg-status-pending-bg text-status-pending'
                  }`}
                >
                  {sync.status === 'success' ? 'Success' : 'Failed'}
                </span>
              </div>
            ))
          ) : (
            <p className="text-center text-neutral-500 py-8">No sync logs yet</p>
          )}
        </div>
      </Card>
    </div>
  )
}


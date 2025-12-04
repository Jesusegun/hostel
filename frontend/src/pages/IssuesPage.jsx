import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams, useNavigate } from 'react-router-dom'
import { format } from 'date-fns'
import Card from '../components/common/Card.jsx'
import Button from '../components/common/Button.jsx'
import StatusBadge from '../components/dashboard/StatusBadge.jsx'
import useAuth from '../hooks/useAuth.js'
import { fetchIssues, updateIssueStatus } from '../services/issueService.js'

const STATUS_OPTIONS = [
  { label: 'All', value: 'all' },
  { label: 'Pending', value: 'pending' },
  { label: 'In Progress', value: 'in_progress' },
  { label: 'Done', value: 'done' },
]

const PAGE_SIZE = 20

export default function IssuesPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  
  // Initialize filters from URL params (for drill-down)
  const initialFilters = useMemo(() => {
    const status = searchParams.get('status') || 'all'
    const hall = searchParams.get('hall') || undefined
    const category = searchParams.get('category') || undefined
    
    return {
      status,
      search: '',
      room_number: '',
      hall: hall,
      category: category,
      page: 1,
      page_size: PAGE_SIZE,
    }
  }, [searchParams])

  const [filters, setFilters] = useState(initialFilters)
  const [data, setData] = useState({ issues: [], total: 0, page: 1, total_pages: 1 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchInput, setSearchInput] = useState(initialFilters.search || '')
  const [roomInput, setRoomInput] = useState(initialFilters.room_number || '')
  const [updatingIssueId, setUpdatingIssueId] = useState(null)
  const [successMessage, setSuccessMessage] = useState(null)
  
  // Update filters when URL params change (e.g., from drill-down)
  useEffect(() => {
    const status = searchParams.get('status') || 'all'
    const hall = searchParams.get('hall') || undefined
    const category = searchParams.get('category') || undefined
    
    setFilters((prev) => ({
      ...prev,
      status,
      hall: hall,
      category: category,
      page: 1,
    }))
  }, [searchParams])

  useEffect(() => {
    setSearchInput(filters.search || '')
  }, [filters.search])

  useEffect(() => {
    setRoomInput(filters.room_number || '')
  }, [filters.room_number])

  useEffect(() => {
    const timer = setTimeout(() => {
      setFilters((prev) => {
        if (prev.search === searchInput) {
          return prev
        }
        return {
          ...prev,
          search: searchInput,
          page: 1,
        }
      })
    }, 500)
    return () => clearTimeout(timer)
  }, [searchInput])

  useEffect(() => {
    const timer = setTimeout(() => {
      setFilters((prev) => {
        if (prev.room_number === roomInput) {
          return prev
        }
        return {
          ...prev,
          room_number: roomInput,
          page: 1,
        }
      })
    }, 500)
    return () => clearTimeout(timer)
  }, [roomInput])

  const loadIssues = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetchIssues(filters)
      setData(response)
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to fetch issues.')
    } finally {
      setLoading(false)
    }
  }, [filters])

  useEffect(() => {
    loadIssues()
  }, [loadIssues])

  useEffect(() => {
    const interval = setInterval(() => {
      loadIssues()
    }, 60000)
    return () => clearInterval(interval)
  }, [loadIssues])

  const handleFilterChange = (name, value) => {
    setFilters((prev) => {
      const newFilters = {
        ...prev,
        [name]: value,
        page: 1,
      }
      
      // Update URL params when filters change (except for search/room_number)
      if (name === 'status' || name === 'hall' || name === 'category') {
        const newParams = new URLSearchParams(searchParams)
        if (value && value !== 'all' && value !== '') {
          newParams.set(name, value)
        } else {
          newParams.delete(name)
        }
        setSearchParams(newParams, { replace: true })
      }
      
      return newFilters
    })
  }
  
  // Clear active filters (breadcrumb-style)
  const clearFilter = (filterName) => {
    const newParams = new URLSearchParams(searchParams)
    newParams.delete(filterName)
    setSearchParams(newParams, { replace: true })
    
    setFilters((prev) => ({
      ...prev,
      [filterName]: filterName === 'status' ? 'all' : undefined,
      search: filterName === 'hall' || filterName === 'category' ? '' : prev.search,
      page: 1,
    }))
  }
  
  // Get active filters for display
  const activeFilters = useMemo(() => {
    const filters = []
    if (searchParams.get('status') && searchParams.get('status') !== 'all') {
      filters.push({ name: 'status', value: searchParams.get('status'), label: `Status: ${searchParams.get('status')}` })
    }
    if (searchParams.get('hall')) {
      filters.push({ name: 'hall', value: searchParams.get('hall'), label: `Hall: ${searchParams.get('hall')}` })
    }
    if (searchParams.get('category')) {
      filters.push({ name: 'category', value: searchParams.get('category'), label: `Category: ${searchParams.get('category')}` })
    }
    return filters
  }, [searchParams])

  const handlePageChange = (direction) => {
    setFilters((prev) => ({
      ...prev,
      page: Math.min(Math.max(1, prev.page + direction), data.total_pages || 1),
    }))
  }

  const paginationSummary = useMemo(() => {
    if (data.total === 0) return 'No issues found'
    const start = (data.page - 1) * PAGE_SIZE + 1
    const end = Math.min(data.page * PAGE_SIZE, data.total)
    return `Showing ${start}-${end} of ${data.total}`
  }, [data])

  const handleMarkDone = async (e, issueId) => {
    e.stopPropagation() // Prevent row click navigation
    setUpdatingIssueId(issueId)
    setSuccessMessage(null)
    try {
      await updateIssueStatus(issueId, 'done')
      setSuccessMessage(`Issue #${issueId} marked as done. Email notification sent.`)
      // Refresh the issues list
      await loadIssues()
      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(null), 3000)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to mark issue as done.')
    } finally {
      setUpdatingIssueId(null)
    }
  }

  // Get current hall name from filters (for breadcrumb)
  const currentHallName = filters.hall || searchParams.get('hall') || null

  return (
    <div className="space-y-6">
      {/* Breadcrumb for admins */}
      {user?.role === 'admin' && (
        <div className="flex items-center gap-2 text-sm">
          <button
            onClick={() => navigate('/hall-selection')}
            className="text-primary-600 hover:text-primary-800 hover:underline font-medium"
          >
            ← Back to Hall Selection
          </button>
          {currentHallName && (
            <>
              <span className="text-neutral-400">/</span>
              <span className="font-semibold text-neutral-700">{currentHallName}</span>
            </>
          )}
        </div>
      )}

      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-neutral-500">
            {user?.role === 'admin' ? 'System Operations' : 'Hall Operations'}
          </p>
          <h2 className="text-3xl font-bold text-neutral-900">
            {currentHallName ? `${currentHallName} - Issues` : 'Issues Board'}
          </h2>
        </div>
        <div className="flex gap-3">
          <Button variant="secondary" onClick={loadIssues}>
            Refresh
          </Button>
        </div>
      </div>

      <Card className="space-y-4">
        {/* Active Filters (Breadcrumb-style) */}
        {activeFilters.length > 0 && (
          <div className="flex flex-wrap items-center gap-2 rounded-lg bg-neutral-50 px-4 py-2">
            <span className="text-sm font-semibold text-neutral-600">Active filters:</span>
            {activeFilters.map((filter) => (
              <span
                key={filter.name}
                className="inline-flex items-center gap-1 rounded-full bg-primary-100 px-3 py-1 text-sm text-primary-700"
              >
                {filter.label}
                <button
                  type="button"
                  onClick={() => clearFilter(filter.name)}
                  className="ml-1 font-bold text-primary-800 hover:text-primary-900"
                  aria-label={`Clear ${filter.name} filter`}
                >
                  ×
                </button>
              </span>
            ))}
            <button
              type="button"
              onClick={() => {
                setSearchParams({}, { replace: true })
                setFilters({
                  status: 'all',
                  search: '',
                  room_number: '',
                  page: 1,
                  page_size: PAGE_SIZE,
                })
              }}
              className="ml-auto text-sm font-semibold text-primary-600 hover:text-primary-700"
            >
              Clear all
            </button>
          </div>
        )}

        <div className="grid gap-4 md:grid-cols-4">
          <input
            type="search"
            placeholder="Search student, description, hall..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="w-full rounded-xl border border-neutral-200 px-4 py-3 text-sm focus:border-primary-500 focus:outline-none md:col-span-2"
          />
          <input
            type="text"
            placeholder="Room number"
            value={roomInput}
            onChange={(e) => setRoomInput(e.target.value)}
            className="rounded-xl border border-neutral-200 px-4 py-3 text-sm focus:border-primary-500 focus:outline-none"
          />
          <select
            value={filters.status}
            onChange={(e) => handleFilterChange('status', e.target.value)}
            className="rounded-xl border border-neutral-200 px-4 py-3 text-sm focus:border-primary-500 focus:outline-none"
          >
            {STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                Status: {option.label}
              </option>
            ))}
          </select>
        </div>

        {error && (
          <div className="rounded-xl border border-status-pending-bg bg-status-pending-bg px-4 py-3 text-sm text-status-pending">
            {error}{' '}
            <button type="button" className="font-semibold underline" onClick={loadIssues}>
              Try again
            </button>
          </div>
        )}

        {successMessage && (
          <div className="rounded-xl border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800">
            {successMessage}
          </div>
        )}

        <div className="overflow-x-auto">
          <table className="w-full min-w-[900px] text-left text-sm">
            <thead>
              <tr className="text-xs uppercase tracking-wide text-neutral-500">
                <th className="py-3">Issue ID</th>
                <th className="py-3">Student Email</th>
                <th className="py-3">Hall / Room</th>
                <th className="py-3">Category</th>
                <th className="py-3">Status</th>
                <th className="py-3">Submitted</th>
                {user?.role === 'hall_admin' && <th className="py-3">Actions</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100">
              {loading &&
                Array.from({ length: 5 }).map((_, index) => (
                  <tr key={index} className="animate-pulse">
                    <td className="py-4">
                      <div className="h-4 w-24 rounded bg-neutral-200" />
                    </td>
                    <td className="py-4">
                      <div className="h-4 w-40 rounded bg-neutral-200" />
                    </td>
                    <td className="py-4">
                      <div className="h-4 w-32 rounded bg-neutral-200" />
                    </td>
                    <td className="py-4">
                      <div className="h-4 w-24 rounded bg-neutral-200" />
                    </td>
                    <td className="py-4">
                      <div className="h-6 w-20 rounded-full bg-neutral-200" />
                    </td>
                    <td className="py-4">
                      <div className="h-4 w-28 rounded bg-neutral-200" />
                    </td>
                    {user?.role === 'hall_admin' && (
                      <td className="py-4">
                        <div className="h-6 w-20 rounded bg-neutral-200" />
                      </td>
                    )}
                  </tr>
                ))}

              {!loading && data.issues.length === 0 && (
                <tr>
                  <td colSpan={user?.role === 'hall_admin' ? 7 : 6} className="py-6 text-center text-neutral-500">
                    No issues match the selected filters.
                  </td>
                </tr>
              )}

              {!loading &&
                data.issues.map((issue) => (
                  <tr 
                    key={issue.id} 
                    className="cursor-pointer transition-colors hover:bg-neutral-50"
                    onClick={() => navigate(`/issues/${issue.id}`)}
                  >
                    <td className="py-4 font-semibold text-neutral-900">#{issue.id}</td>
                    <td className="py-4 text-neutral-700">{issue.student_email}</td>
                    <td className="py-4 text-neutral-700">
                      {issue.hall_name} • Room {issue.room_number}
                    </td>
                    <td className="py-4 text-neutral-700">{issue.category_name}</td>
                    <td className="py-4">
                      <StatusBadge status={issue.status} />
                    </td>
                    <td className="py-4 text-neutral-500">
                      {issue.created_at ? format(new Date(issue.created_at), 'dd MMM yyyy HH:mm') : '—'}
                    </td>
                    {user?.role === 'hall_admin' && (
                      <td className="py-4" onClick={(e) => e.stopPropagation()}>
                        {issue.status !== 'done' && (
                          <Button
                            variant="ghost"
                            className="text-xs px-3 py-1.5"
                            onClick={(e) => handleMarkDone(e, issue.id)}
                            disabled={updatingIssueId === issue.id}
                          >
                            {updatingIssueId === issue.id ? 'Marking...' : 'Mark Done'}
                          </Button>
                        )}
                      </td>
                    )}
                  </tr>
                ))}
            </tbody>
          </table>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-neutral-100 pt-4 text-sm text-neutral-600">
          <p>{paginationSummary}</p>
          <div className="flex items-center gap-2">
            <Button variant="secondary" onClick={() => handlePageChange(-1)} disabled={data.page <= 1 || loading}>
              Previous
            </Button>
            <span>
              Page {data.page} / {data.total_pages || 1}
            </span>
            <Button
              variant="secondary"
              onClick={() => handlePageChange(1)}
              disabled={data.page >= (data.total_pages || 1) || loading}
            >
              Next
            </Button>
          </div>
        </div>
      </Card>
    </div>
  )
}


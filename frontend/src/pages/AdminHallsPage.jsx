import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Card from '../components/common/Card.jsx'
import Button from '../components/common/Button.jsx'
import { fetchAllHalls, createHallWithAdmin } from '../services/adminService.js'
import useAuth from '../hooks/useAuth.js'

export default function AdminHallsPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [halls, setHalls] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showPasswordModal, setShowPasswordModal] = useState(false)
  const [passwordData, setPasswordData] = useState(null)
  const [creating, setCreating] = useState(false)
  
  // Form state
  const [formData, setFormData] = useState({
    hall_name: '',
    password: '',
  })

  useEffect(() => {
    loadHalls()
  }, [])

  const loadHalls = async () => {
    try {
      setLoading(true)
      setError(null)
      const hallsData = await fetchAllHalls()
      setHalls(hallsData)
    } catch (err) {
      console.error('Failed to load halls:', err)
      setError('Failed to load halls. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateHall = async (e) => {
    e.preventDefault()
    try {
      setCreating(true)
      setError(null)
      
      const data = {
        hall_name: formData.hall_name.trim(),
        password: formData.password.trim() || undefined,
      }
      
      const result = await createHallWithAdmin(data)
      
      // Show password in modal
      setPasswordData({
        hall: result.hall.name,
        username: result.user.username,
        password: result.password,
      })
      setShowCreateModal(false)
      setShowPasswordModal(true)
      
      // Reset form
      setFormData({
        hall_name: '',
        password: '',
      })
      
      // Reload halls list
      await loadHalls()
    } catch (err) {
      console.error('Failed to create hall:', err)
      setError(err.response?.data?.detail || 'Failed to create hall. Please try again.')
    } finally {
      setCreating(false)
    }
  }

  const handleHallClick = (hallName) => {
    navigate(`/issues?hall=${encodeURIComponent(hallName)}`)
  }

  const copyPassword = () => {
    if (passwordData?.password) {
      navigator.clipboard.writeText(passwordData.password)
      alert('Password copied to clipboard!')
    }
  }

  // Generate username from hall name (for display only)
  const generateUsername = (hallName) => {
    if (!hallName) return ''
    return hallName.toLowerCase().replace(/\s+/g, '').replace(/-/g, '').replace(/_/g, '').replace(/[^a-z0-9]/g, '')
  }

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="text-neutral-500">Loading halls...</div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-neutral-900">Hall Management</h2>
          <p className="mt-1 text-sm text-neutral-500">Manage halls and their admin users</p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>Create Hall</Button>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 p-4 text-sm text-red-600">
          {error}
        </div>
      )}

      <Card>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="border-b border-neutral-200 bg-neutral-50 text-left text-xs font-semibold uppercase tracking-wider text-neutral-600">
              <tr>
                <th className="rounded-tl-xl px-4 py-3">Hall Name</th>
                <th className="px-4 py-3 text-center">Total Issues</th>
                <th className="px-4 py-3 text-center">Pending</th>
                <th className="px-4 py-3 text-center">In Progress</th>
                <th className="px-4 py-3 text-center">Done</th>
                <th className="rounded-tr-xl px-4 py-3">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100">
              {halls.length === 0 ? (
                <tr>
                  <td colSpan="6" className="px-4 py-8 text-center text-neutral-500">
                    No halls found.
                  </td>
                </tr>
              ) : (
                halls.map((hall) => (
                  <tr
                    key={hall.id}
                    className="cursor-pointer transition-colors hover:bg-neutral-50"
                    onClick={() => handleHallClick(hall.name)}
                  >
                    <td className="px-4 py-4 text-sm font-semibold text-neutral-900">
                      {hall.name}
                    </td>
                    <td className="px-4 py-4 text-center text-sm font-medium text-neutral-900">
                      {hall.total}
                    </td>
                    <td className="px-4 py-4 text-center text-sm text-status-pending">
                      {hall.pending}
                    </td>
                    <td className="px-4 py-4 text-center text-sm text-status-in-progress">
                      {hall.in_progress}
                    </td>
                    <td className="px-4 py-4 text-center text-sm text-status-done">
                      {hall.done}
                    </td>
                    <td className="px-4 py-4 text-sm text-neutral-500">
                      {hall.created_at ? new Date(hall.created_at).toLocaleDateString() : '-'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Create Hall Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-md">
            <h3 className="text-xl font-bold text-neutral-900">Create Hall with Admin</h3>
            <form onSubmit={handleCreateHall} className="mt-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-neutral-700">
                  Hall Name *
                </label>
                <input
                  type="text"
                  required
                  value={formData.hall_name}
                  onChange={(e) => setFormData({ ...formData, hall_name: e.target.value })}
                  className="mt-1 w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                  placeholder="New Hall"
                />
                <p className="mt-1 text-xs text-neutral-500">
                  Username will be auto-generated: <span className="font-mono font-semibold">{generateUsername(formData.hall_name) || '...'}</span>
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-neutral-700">
                  Password (optional - auto-generated if empty)
                </label>
                <input
                  type="text"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="mt-1 w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                  placeholder="Leave empty to auto-generate"
                  minLength={8}
                />
              </div>
              
              <div className="flex gap-3 pt-4">
                <Button
                  type="button"
                  variant="ghost"
                  className="flex-1"
                  onClick={() => setShowCreateModal(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" className="flex-1" disabled={creating}>
                  {creating ? 'Creating...' : 'Create Hall'}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}

      {/* Password Display Modal */}
      {showPasswordModal && passwordData && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-md">
            <h3 className="text-xl font-bold text-neutral-900">Hall Created Successfully</h3>
            <div className="mt-6 space-y-4">
              <div className="rounded-lg bg-neutral-50 p-4">
                <p className="text-sm text-neutral-600">Hall:</p>
                <p className="text-lg font-semibold text-neutral-900">{passwordData.hall}</p>
              </div>
              <div className="rounded-lg bg-neutral-50 p-4">
                <p className="text-sm text-neutral-600">Username:</p>
                <p className="text-lg font-semibold text-neutral-900">{passwordData.username}</p>
              </div>
              <div className="rounded-lg bg-neutral-50 p-4">
                <p className="text-sm text-neutral-600">Password:</p>
                <p className="text-lg font-mono font-semibold text-neutral-900">{passwordData.password}</p>
              </div>
              <div className="rounded-lg bg-yellow-50 p-3 text-sm text-yellow-800">
                ⚠️ Save this password. It won't be shown again.
              </div>
              <div className="flex gap-3 pt-4">
                <Button
                  variant="ghost"
                  className="flex-1"
                  onClick={copyPassword}
                >
                  Copy Password
                </Button>
                <Button
                  className="flex-1"
                  onClick={() => {
                    setShowPasswordModal(false)
                    setPasswordData(null)
                  }}
                >
                  Close
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}


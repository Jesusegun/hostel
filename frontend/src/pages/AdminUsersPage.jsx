import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Card from '../components/common/Card.jsx'
import Button from '../components/common/Button.jsx'
import { fetchAllUsers, resetUserPassword, unlockUser } from '../services/adminService.js'
import useAuth from '../hooks/useAuth.js'
import { formatUsername } from '../utils/formatUsername.js'

export default function AdminUsersPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  // Redirect if not DSA
  useEffect(() => {
    if (user && user.username !== 'dsa') {
      navigate('/dashboard')
    }
  }, [user, navigate])
  const [showPasswordModal, setShowPasswordModal] = useState(false)
  const [passwordData, setPasswordData] = useState(null)
  const [resetting, setResetting] = useState(false)
  const [unlocking, setUnlocking] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      const usersData = await fetchAllUsers()
      setUsers(usersData || [])
    } catch (err) {
      console.error('Failed to load data:', err)
      let errorMessage = 'Failed to load users. Please try again.'
      
      if (err.response?.status === 403) {
        errorMessage = 'Access denied. Only DSA can access this page.'
      } else if (err.response?.status === 401) {
        errorMessage = 'Please log in to access this page.'
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail
      } else if (err.message) {
        errorMessage = err.message
      }
      
      setError(errorMessage)
      console.error('Error details:', {
        status: err.response?.status,
        data: err.response?.data,
        message: err.message,
      })
    } finally {
      setLoading(false)
    }
  }

  const handleResetPassword = async (userId) => {
    if (!confirm('Are you sure you want to reset this user\'s password?')) {
      return
    }
    
    try {
      setResetting(true)
      setError(null)
      
      const result = await resetUserPassword(userId)
      
      // Show password in modal
      setPasswordData({
        username: result.username,
        password: result.new_password,
      })
      setShowPasswordModal(true)
      
      // Reload users list
      await loadData()
    } catch (err) {
      console.error('Failed to reset password:', err)
      setError(err.response?.data?.detail || 'Failed to reset password. Please try again.')
    } finally {
      setResetting(false)
    }
  }

  const handleSetSecurityQuestion = () => {
    navigate('/set-security-question')
  }

  const handleUnlockUser = async (userId, username) => {
    if (!confirm(`Are you sure you want to unlock ${username}'s account?`)) {
      return
    }
    
    try {
      setUnlocking(true)
      setError(null)
      
      await unlockUser(userId)
      
      // Reload users list
      await loadData()
    } catch (err) {
      console.error('Failed to unlock user:', err)
      setError(err.response?.data?.detail || 'Failed to unlock user. Please try again.')
    } finally {
      setUnlocking(false)
    }
  }

  const copyPassword = () => {
    if (passwordData?.password) {
      navigator.clipboard.writeText(passwordData.password)
      alert('Password copied to clipboard!')
    }
  }

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="text-neutral-500">Loading users...</div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-neutral-900">User Management</h2>
          <p className="mt-1 text-sm text-neutral-500">Manage hall admin users</p>
        </div>
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
                <th className="rounded-tl-xl px-4 py-3">Username</th>
                <th className="px-4 py-3">Role</th>
                <th className="px-4 py-3">Hall</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Created</th>
                <th className="rounded-tr-xl px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100">
              {error ? (
                <tr>
                  <td colSpan="6" className="px-4 py-8 text-center text-red-600">
                    {error}
                  </td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan="6" className="px-4 py-8 text-center text-neutral-500">
                    No users found.
                  </td>
                </tr>
              ) : (
                users.map((user) => (
                  <tr key={user.id} className="hover:bg-neutral-50">
                    <td className="px-4 py-4 text-sm font-medium text-neutral-900">
                      {formatUsername(user.username)}
                    </td>
                    <td className="px-4 py-4 text-sm text-neutral-600">
                      <span className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${
                        user.role === 'admin' 
                          ? 'bg-blue-100 text-blue-800' 
                          : 'bg-green-100 text-green-800'
                      }`}>
                        {user.role === 'admin' ? 'Admin' : 'Hall Admin'}
                      </span>
                    </td>
                    <td className="px-4 py-4 text-sm text-neutral-600">
                      {user.hall_name || '-'}
                    </td>
                    <td className="px-4 py-4 text-sm text-neutral-600">
                      {user.is_locked ? (
                        <span className="inline-flex items-center gap-1 rounded-full bg-red-100 px-2 py-1 text-xs font-semibold text-red-800">
                          🔒 Locked ({user.lockout_remaining_minutes}m)
                        </span>
                      ) : (
                        <span className="inline-flex rounded-full bg-green-100 px-2 py-1 text-xs font-semibold text-green-800">
                          Active
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-4 text-sm text-neutral-500">
                      {user.created_at ? new Date(user.created_at).toLocaleDateString() : '-'}
                    </td>
                    <td className="px-4 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {user.is_locked && (
                          <Button
                            variant="outline"
                            className="text-sm text-red-600 hover:bg-red-50"
                            onClick={() => handleUnlockUser(user.id, user.username)}
                            disabled={unlocking}
                          >
                            Unlock
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          className="text-sm"
                          onClick={() => handleResetPassword(user.id)}
                          disabled={resetting}
                        >
                          Reset Password
                        </Button>
                        {user.username === 'dsa' && (
                          <Button
                            variant="outline"
                            className="text-sm"
                            onClick={handleSetSecurityQuestion}
                          >
                            Set Security Question
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Password Display Modal */}
      {showPasswordModal && passwordData && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-md">
            <h3 className="text-xl font-bold text-neutral-900">Password Generated</h3>
            <div className="mt-6 space-y-4">
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


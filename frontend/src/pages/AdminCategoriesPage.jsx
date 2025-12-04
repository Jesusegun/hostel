import { useState, useEffect, useMemo } from 'react'
import Card from '../components/common/Card.jsx'
import Button from '../components/common/Button.jsx'
import {
  fetchAllCategories,
  createCategory,
  updateCategory,
  deleteCategory,
  activateCategory,
} from '../services/adminService.js'
import useAuth from '../hooks/useAuth.js'

export default function AdminCategoriesPage() {
  const { user } = useAuth()
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingCategory, setEditingCategory] = useState(null)
  const [creating, setCreating] = useState(false)
  const [updating, setUpdating] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [reactivating, setReactivating] = useState(false)
  const [statusFilter, setStatusFilter] = useState('active')
  
  // Form state
  const [formData, setFormData] = useState({
    name: '',
  })

  useEffect(() => {
    loadCategories()
  }, [])

  const loadCategories = async () => {
    try {
      setLoading(true)
      setError(null)
      const categoriesData = await fetchAllCategories()
      setCategories(categoriesData)
    } catch (err) {
      console.error('Failed to load categories:', err)
      setError('Failed to load categories. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateCategory = async (e) => {
    e.preventDefault()
    try {
      setCreating(true)
      setError(null)
      
      await createCategory(formData.name.trim())
      
      setShowCreateModal(false)
      setFormData({ name: '' })
      await loadCategories()
    } catch (err) {
      console.error('Failed to create category:', err)
      setError(err.response?.data?.detail || 'Failed to create category. Please try again.')
    } finally {
      setCreating(false)
    }
  }

  const handleUpdateCategory = async (e) => {
    e.preventDefault()
    try {
      setUpdating(true)
      setError(null)
      
      await updateCategory(editingCategory.id, formData.name.trim())
      
      setEditingCategory(null)
      setFormData({ name: '' })
      await loadCategories()
    } catch (err) {
      console.error('Failed to update category:', err)
      setError(err.response?.data?.detail || 'Failed to update category. Please try again.')
    } finally {
      setUpdating(false)
    }
  }

  const handleDeleteCategory = async (categoryId, categoryName) => {
    if (
      !confirm(
        `Hide "${categoryName}"? This removes it from forms going forward but keeps historical issues intact. You can reactivate it anytime.`,
      )
    ) {
      return
    }
    
    try {
      setDeleting(true)
      setError(null)
      
      await deleteCategory(categoryId)
      await loadCategories()
    } catch (err) {
      console.error('Failed to delete category:', err)
      setError(err.response?.data?.detail || 'Failed to delete category. Please try again.')
    } finally {
      setDeleting(false)
    }
  }

  const startEdit = (category) => {
    setEditingCategory(category)
    setFormData({ name: category.name })
  }

  const cancelEdit = () => {
    setEditingCategory(null)
    setFormData({ name: '' })
  }

  const handleReactivateCategory = async (categoryId) => {
    try {
      setReactivating(true)
      setError(null)
      await activateCategory(categoryId)
      await loadCategories()
    } catch (err) {
      console.error('Failed to activate category:', err)
      setError(err.response?.data?.detail || 'Failed to activate category. Please try again.')
    } finally {
      setReactivating(false)
    }
  }

  const activeCount = categories.filter((category) => category.is_active).length
  const inactiveCount = categories.length - activeCount

  const filteredCategories = categories.filter((category) => {
    if (statusFilter === 'active') return category.is_active
    if (statusFilter === 'inactive') return !category.is_active
    return true
  })

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center">
        <div className="text-neutral-500">Loading categories...</div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-neutral-900">Category Management</h2>
          <p className="mt-1 text-sm text-neutral-500">Manage issue categories</p>
        </div>
        <div className="flex gap-2 rounded-xl bg-neutral-100 p-1 text-sm font-semibold">
          {[
            { label: `Active (${activeCount})`, value: 'active' },
            { label: `Hidden (${inactiveCount})`, value: 'inactive' },
            { label: `All (${categories.length})`, value: 'all' },
          ].map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => setStatusFilter(option.value)}
              className={`rounded-lg px-3 py-1 transition ${
                statusFilter === option.value
                  ? 'bg-white text-neutral-900 shadow'
                  : 'text-neutral-500 hover:text-neutral-900'
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
        <Button onClick={() => setShowCreateModal(true)}>Create Category</Button>
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
                <th className="rounded-tl-xl px-4 py-3">Category Name</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Created</th>
                <th className="rounded-tr-xl px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-100">
              {filteredCategories.length === 0 ? (
                <tr>
                  <td colSpan="4" className="px-4 py-8 text-center text-neutral-500">
                    {statusFilter === 'active'
                      ? 'No active categories.'
                      : statusFilter === 'inactive'
                        ? 'No hidden categories.'
                        : 'No categories found.'}
                  </td>
                </tr>
              ) : (
                filteredCategories.map((category) => (
                  <tr
                    key={category.id}
                    className={`hover:bg-neutral-50 ${!category.is_active ? 'opacity-60' : ''}`}
                  >
                    <td className="px-4 py-4 text-sm font-medium text-neutral-900">
                      {category.name}
                    </td>
                    <td className="px-4 py-4">
                      <span className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${
                        category.is_active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {category.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-4 py-4 text-sm text-neutral-500">
                      {category.created_at ? new Date(category.created_at).toLocaleDateString() : '-'}
                    </td>
                    <td className="px-4 py-4 text-right">
                      <div className="flex justify-end gap-2">
                        {category.is_active ? (
                          <>
                            <Button
                              variant="ghost"
                              className="text-sm"
                              onClick={() => startEdit(category)}
                            >
                              Edit
                            </Button>
                            <Button
                              variant="ghost"
                              className="text-sm text-red-600 hover:text-red-700"
                              onClick={() => handleDeleteCategory(category.id, category.name)}
                              disabled={deleting}
                            >
                              Hide
                            </Button>
                          </>
                        ) : (
                          <Button
                            variant="ghost"
                            className="text-sm text-primary-600 hover:text-primary-700"
                            onClick={() => handleReactivateCategory(category.id)}
                            disabled={reactivating}
                          >
                            Activate
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

      {/* Create Category Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-md">
            <h3 className="text-xl font-bold text-neutral-900">Create Category</h3>
            <form onSubmit={handleCreateCategory} className="mt-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-neutral-700">
                  Category Name *
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ name: e.target.value })}
                  className="mt-1 w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                  placeholder="New Category"
                />
              </div>
              
              <div className="flex gap-3 pt-4">
                <Button
                  type="button"
                  variant="ghost"
                  className="flex-1"
                  onClick={() => {
                    setShowCreateModal(false)
                    setFormData({ name: '' })
                  }}
                >
                  Cancel
                </Button>
                <Button type="submit" className="flex-1" disabled={creating}>
                  {creating ? 'Creating...' : 'Create Category'}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}

      {/* Edit Category Modal */}
      {editingCategory && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-md">
            <h3 className="text-xl font-bold text-neutral-900">Edit Category</h3>
            <form onSubmit={handleUpdateCategory} className="mt-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-neutral-700">
                  Category Name *
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ name: e.target.value })}
                  className="mt-1 w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                />
              </div>
              
              <div className="flex gap-3 pt-4">
                <Button
                  type="button"
                  variant="ghost"
                  className="flex-1"
                  onClick={cancelEdit}
                >
                  Cancel
                </Button>
                <Button type="submit" className="flex-1" disabled={updating}>
                  {updating ? 'Updating...' : 'Update Category'}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  )
}


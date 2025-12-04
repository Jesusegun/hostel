/**
 * Admin Service
 * 
 * API service functions for admin management operations (DSA only).
 * Handles user management, hall management, and category management.
 */

import api from './api'

// ===== User Management =====

/**
 * Get all users in the system
 * @returns {Promise<Array>} List of all users
 */
export const fetchAllUsers = async () => {
  const response = await api.get('/admin/users')
  return response.data
}

/**
 * Create a new hall admin user
 * @param {Object} data - User data
 * @param {number} data.hall_id - ID of the hall
 * @param {string} data.username - Username for the admin
 * @param {string} [data.password] - Optional password (auto-generated if not provided)
 * @param {string} [data.email] - Optional email address
 * @returns {Promise<Object>} Created user and password
 */
export const createHallAdmin = async (data) => {
  const response = await api.post('/admin/users', data)
  return response.data
}

/**
 * Reset a user's password
 * @param {number} userId - ID of the user
 * @returns {Promise<Object>} New password in plain text
 */
export const resetUserPassword = async (userId) => {
  const response = await api.put(`/admin/users/${userId}/password`)
  return response.data
}

/**
 * Unlock a user's account (clear lockout)
 * @param {number} userId - ID of the user
 * @returns {Promise<Object>} Success message
 */
export const unlockUser = async (userId) => {
  const response = await api.post(`/admin/users/${userId}/unlock`)
  return response.data
}

// ===== Hall Management =====

/**
 * Get all halls with issue statistics
 * @returns {Promise<Array>} List of all halls with stats
 */
export const fetchAllHalls = async () => {
  const response = await api.get('/admin/halls')
  return response.data
}

/**
 * Create a new hall with admin user
 * @param {Object} data - Hall and user data
 * @param {string} data.hall_name - Name of the hall
 * @param {string} data.username - Username for the hall admin
 * @param {string} [data.password] - Optional password (auto-generated if not provided)
 * @param {string} [data.email] - Optional email address
 * @returns {Promise<Object>} Created hall, user, and password
 */
export const createHallWithAdmin = async (data) => {
  const response = await api.post('/admin/halls', data)
  return response.data
}

// ===== Category Management =====

/**
 * Get all categories (active and inactive)
 * @returns {Promise<Array>} List of all categories
 */
export const fetchAllCategories = async () => {
  const response = await api.get('/admin/categories')
  return response.data
}

/**
 * Create a new category
 * @param {string} name - Category name
 * @returns {Promise<Object>} Created category
 */
export const createCategory = async (name) => {
  const response = await api.post('/admin/categories', { name })
  return response.data
}

/**
 * Update a category's name
 * @param {number} categoryId - ID of the category
 * @param {string} name - New category name
 * @returns {Promise<Object>} Updated category
 */
export const updateCategory = async (categoryId, name) => {
  const response = await api.put(`/admin/categories/${categoryId}`, { name })
  return response.data
}

/**
 * Soft delete a category (set is_active to false)
 * @param {number} categoryId - ID of the category
 * @returns {Promise<Object>} Updated category
 */
export const deleteCategory = async (categoryId) => {
  const response = await api.delete(`/admin/categories/${categoryId}`)
  return response.data
}

/**
 * Reactivate a soft-deleted category (set is_active to true)
 * @param {number} categoryId - ID of the category
 * @returns {Promise<Object>} Updated category
 */
export const activateCategory = async (categoryId) => {
  const response = await api.post(`/admin/categories/${categoryId}/activate`)
  return response.data
}

// ===== Password Recovery =====

/**
 * Get security question for a user
 * @param {string} username - Username
 * @returns {Promise<Object>} Security question response
 */
export const getSecurityQuestion = async (username) => {
  const response = await api.post('/auth/security-question', { username })
  return response.data
}

/**
 * Verify security answer and reset password
 * @param {Object} data - Reset data
 * @param {string} data.username - Username
 * @param {string} data.answer - Security answer
 * @param {string} data.new_password - New password
 * @returns {Promise<Object>} Success message
 */
export const verifySecurityAnswer = async (data) => {
  const response = await api.post('/auth/verify-security-answer', data)
  return response.data
}

/**
 * Set security question for current user (DSA only)
 * @param {Object} data - Security question data
 * @param {string} data.question - Security question
 * @param {string} data.answer - Security answer
 * @returns {Promise<Object>} Success message
 */
export const setSecurityQuestion = async (data) => {
  const response = await api.post('/auth/set-security-question', data)
  return response.data
}


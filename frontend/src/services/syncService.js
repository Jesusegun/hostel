import api from './api.js'
import axios from 'axios'

/**
 * Fetch sync status and history from the backend.
 *
 * @returns {Promise<Object>} Sync status including last_sync, recent_syncs, and total_syncs
 */
export async function fetchSyncStatus() {
  const { data } = await api.get('/sync/status')
  return data
}

/**
 * Manually trigger a Google Sheets sync.
 * 
 * Uses a longer timeout (120 seconds) because sync can take time,
 * especially when processing many rows or uploading images.
 * 
 * @returns {Promise<Object>} Sync result with status, rows_processed, rows_created, etc.
 */
export async function triggerManualSync() {
  // Create a custom axios instance with longer timeout for sync
  // Sync can take 30-120+ seconds depending on data volume and network
  // Default timeout is 15 seconds, which is too short for sync operations
  const syncApi = axios.create({
    baseURL: api.defaults.baseURL,
    timeout: 120000, // 120 seconds (2 minutes) - enough for most syncs
  })
  
  // Add request interceptor to copy auth token from main api instance
  syncApi.interceptors.request.use((config) => {
    // Get auth token from localStorage (same key used by AuthContext: 'hrs_token')
    const token = localStorage.getItem('hrs_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  })
  
  // Add response interceptor to handle 401 (same as main api)
  syncApi.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        // Clear token on unauthorized (same as main api)
        localStorage.removeItem('hrs_token')
        localStorage.removeItem('hrs_user')
      }
      return Promise.reject(error)
    }
  )
  
  const { data } = await syncApi.post('/sync/google-sheets')
  return data
}


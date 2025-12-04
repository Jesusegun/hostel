import api from './api.js'

/**
 * Fetch admin dashboard summary with optional date range filtering.
 *
 * @param {Object} options - Optional parameters
 * @param {string} options.dateFrom - Start date (ISO format: YYYY-MM-DD)
 * @param {string} options.dateTo - End date (ISO format: YYYY-MM-DD)
 * @returns {Promise<Object>} Dashboard summary data
 */
export async function fetchAdminDashboardSummary({ dateFrom, dateTo } = {}) {
  const params = {}
  if (dateFrom) {
    params.date_from = dateFrom
  }
  if (dateTo) {
    params.date_to = dateTo
  }
  const { data } = await api.get('/dashboard/summary', { params })
  return data
}



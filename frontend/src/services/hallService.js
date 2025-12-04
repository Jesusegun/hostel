import api from './api.js'

/**
 * Fetch all halls with issue statistics.
 *
 * @returns {Promise<Array>} List of halls with issue counts
 */
export async function fetchHallsWithStats() {
  const { data } = await api.get('/halls')
  return data
}


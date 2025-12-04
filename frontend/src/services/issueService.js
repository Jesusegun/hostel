import api from './api.js'

const buildQueryString = (filters = {}) => {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '' && value !== 'all') {
      params.append(key, value)
    }
  })
  return params.toString()
}

export async function fetchIssues(filters = {}) {
  const query = buildQueryString(filters)
  const { data } = await api.get(`/issues${query ? `?${query}` : ''}`)
  return data
}

export async function fetchIssueById(issueId) {
  const { data } = await api.get(`/issues/${issueId}`)
  return data
}

export async function updateIssueStatus(issueId, status) {
  const { data } = await api.put(`/issues/${issueId}/status`, { status })
  return data
}

export async function fetchIssueStats() {
  const { data } = await api.get('/issues/stats')
  return data
}


import api from './api.js'

const formHeaders = { 'Content-Type': 'application/x-www-form-urlencoded' }

export async function login(credentials) {
  const params = new URLSearchParams()
  params.append('username', credentials.username)
  params.append('password', credentials.password)

  const { data } = await api.post('/auth/login', params, { headers: formHeaders })
  return data
}

export async function fetchCurrentUser() {
  const { data } = await api.get('/auth/me')
  return data
}

export async function logout() {
  await api.post('/auth/logout')
}


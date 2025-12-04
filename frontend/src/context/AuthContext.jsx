/* eslint-disable react-refresh/only-export-components */
import { createContext, useCallback, useMemo, useState } from 'react'
import PropTypes from 'prop-types'
import { clearAuthToken, setAuthToken } from '../services/api.js'
import { fetchCurrentUser, login as loginRequest, logout as logoutRequest } from '../services/authService.js'

export const AuthContext = createContext({
  user: null,
  token: null,
  loading: false,
  isAuthenticated: false,
  login: async () => {},
  logout: () => {},
  refreshProfile: async () => {},
})

const USER_KEY = 'hrs_user'
const TOKEN_KEY = 'hrs_token'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const cached = localStorage.getItem(USER_KEY)
      return cached ? JSON.parse(cached) : null
    } catch {
      return null
    }
  })
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY))
  const [loading, setLoading] = useState(false)

  if (token) {
    setAuthToken(token)
  }

  const persistSession = useCallback((nextToken, nextUser) => {
    if (nextToken) {
      localStorage.setItem(TOKEN_KEY, nextToken)
      setAuthToken(nextToken)
      setToken(nextToken)
    }
    if (nextUser) {
      localStorage.setItem(USER_KEY, JSON.stringify(nextUser))
      setUser(nextUser)
    }
  }, [])

  const clearSession = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    clearAuthToken()
    setToken(null)
    setUser(null)
  }, [])

  const login = useCallback(
    async (credentials) => {
      setLoading(true)
      try {
        const data = await loginRequest(credentials)
        persistSession(data.access_token, data.user)
        return data
      } finally {
        setLoading(false)
      }
    },
    [persistSession],
  )

  const logout = useCallback(async () => {
    try {
      await logoutRequest()
    } catch (error) {
      console.warn('Logout request failed', error)
    } finally {
      clearSession()
    }
  }, [clearSession])

  const refreshProfile = useCallback(async () => {
    if (!token) return null
    setLoading(true)
    try {
      const profile = await fetchCurrentUser()
      setUser(profile)
      localStorage.setItem(USER_KEY, JSON.stringify(profile))
      return profile
    } finally {
      setLoading(false)
    }
  }, [token])

  const value = useMemo(
    () => ({
      user,
      token,
      loading,
      isAuthenticated: Boolean(user && token),
      login,
      logout,
      refreshProfile,
    }),
    [user, token, loading, login, logout, refreshProfile],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

AuthProvider.propTypes = {
  children: PropTypes.node.isRequired,
}


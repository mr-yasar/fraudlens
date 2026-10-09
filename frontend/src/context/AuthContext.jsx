import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => {
    try {
      return localStorage.getItem('fraudlens_token') || null
    } catch {
      return null
    }
  })
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem('fraudlens_user')
      return saved ? JSON.parse(saved) : null
    } catch {
      return null
    }
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const login = async (email, password) => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `Login failed: HTTP ${response.status}`)
      }

      const data = await response.json()
      const userPayload = {
        id: data.user_id,
        email: data.email,
        name: data.name,
        role: data.role,
        account_tier: data.account_tier || 'STANDARD',
      }
      setToken(data.access_token)
      setUser(userPayload)

      localStorage.setItem('fraudlens_token', data.access_token)
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('fraudlens_user', JSON.stringify(userPayload))
      return data
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Authentication failed'
      setError(msg)
      throw err
    } finally {
      setLoading(false)
    }
  }

  const register = async (name, email, password) => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({ name, email, password }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `Registration failed: HTTP ${response.status}`)
      }

      const data = await response.json()
      const userPayload = {
        id: data.user_id,
        email: data.email,
        name: data.name,
        role: data.role,
        account_tier: data.account_tier || 'STANDARD',
      }
      setToken(data.access_token)
      setUser(userPayload)

      localStorage.setItem('fraudlens_token', data.access_token)
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('fraudlens_user', JSON.stringify(userPayload))
      return data
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Registration failed'
      setError(msg)
      throw err
    } finally {
      setLoading(false)
    }
  }

  const logout = useCallback(() => {
    setToken(null)
    setUser(null)
    setError(null)
    localStorage.removeItem('fraudlens_token')
    localStorage.removeItem('access_token')
    localStorage.removeItem('fraudlens_user')
    // Clear sessionStorage to prevent data leakage on back-button
    try { sessionStorage.clear() } catch {}
    // Replace history state to prevent back-button re-entry
    try { window.history.replaceState(null, '', window.location.pathname) } catch {}
  }, [])

  // Verify token on mount and synchronize current user profile
  useEffect(() => {
    if (!token) return

    fetch('/api/v1/auth/me', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Accept': 'application/json',
      },
    })
      .then((res) => {
        if (!res.ok) {
          logout()
          return null
        }
        return res.json()
      })
      .then((userData) => {
        if (userData) {
          const syncedUser = {
            id: userData.id,
            email: userData.email,
            name: userData.name,
            role: userData.role,
            account_tier: userData.account_tier || 'STANDARD',
          }
          setUser(syncedUser)
          localStorage.setItem('fraudlens_user', JSON.stringify(syncedUser))
        }
      })
      .catch(() => {})
  }, [token, logout])

  // Listen for session expiration events and immediately reset auth state
  useEffect(() => {
    const handleExpired = () => {
      logout()
    }
    window.addEventListener('fraudlens:auth_expired', handleExpired)
    return () => window.removeEventListener('fraudlens:auth_expired', handleExpired)
  }, [logout])

  const isAuthenticated = !!token && !!user
  const userRole = (user?.role || '').toUpperCase()
  const userEmail = (user?.email || '').toLowerCase()
  // Strict admin check: exact role match or exact admin domain email only
  const isAdmin = userRole === 'ADMIN' || userEmail === 'admin@fraudlens.internal'
  const isInvestigator = userRole === 'FRAUD_INVESTIGATOR' || isAdmin

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        role: user?.role,
        isAuthenticated,
        isAdmin,
        isInvestigator,
        loading,
        error,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

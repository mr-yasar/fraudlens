import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('fraudlens_token') || null)
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('fraudlens_user')
    return saved ? JSON.parse(saved) : null
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
      setToken(data.access_token)
      setUser({
        id: data.user_id,
        email: data.email,
        name: data.name,
        role: data.role,
      })

      localStorage.setItem('fraudlens_token', data.access_token)
      localStorage.setItem(
        'fraudlens_user',
        JSON.stringify({
          id: data.user_id,
          email: data.email,
          name: data.name,
          role: data.role,
        })
      )
      return data
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Authentication failed'
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
    localStorage.removeItem('fraudlens_user')
  }, [])

  // Verify token on mount
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
        }
      })
      .catch(() => {})
  }, [token, logout])

  const isAuthenticated = !!token && !!user
  const isAdmin = user?.role === 'ADMIN'
  const isInvestigator = user?.role === 'FRAUD_INVESTIGATOR' || isAdmin

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

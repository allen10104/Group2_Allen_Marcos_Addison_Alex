import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import * as authApi from '../api/auth'
import { getAccessToken, setAccessToken } from '../api/client'
import type { User } from '../types'

interface AuthContextValue {
  user: User | null
  token: string | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(getAccessToken())
  const [isLoading, setIsLoading] = useState(true)

  const loadUser = useCallback(async () => {
    const stored = getAccessToken()
    if (!stored) {
      setUser(null)
      setToken(null)
      setIsLoading(false)
      return
    }

    try {
      const me = await authApi.fetchCurrentUser()
      setUser(me)
      setToken(stored)
    } catch {
      setAccessToken(null)
      setUser(null)
      setToken(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadUser()
  }, [loadUser])

  const login = useCallback(async (email: string, password: string) => {
    const accessToken = await authApi.login(email, password)
    setToken(accessToken)
    const me = await authApi.fetchCurrentUser()
    setUser(me)
  }, [])

  const logout = useCallback(() => {
    authApi.logout()
    setUser(null)
    setToken(null)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      isLoading,
      isAuthenticated: Boolean(user && token),
      login,
      logout,
    }),
    [user, token, isLoading, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return ctx
}

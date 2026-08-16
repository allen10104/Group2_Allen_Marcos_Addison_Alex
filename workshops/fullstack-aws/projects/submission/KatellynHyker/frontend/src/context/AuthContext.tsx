/**
 * React Auth Context -- single source of truth for "who is logged in?"
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { loginRequest, registerRequest } from '../api/auth'
import { AUTH_UNAUTHORIZED_EVENT, authStorage, getApiErrorMessage } from '../api/client'
import type { LoginCredentials, RegisterCredentials, User } from '../types/auth'

type AuthContextValue = {
  user: User | null
  isAuthenticated: boolean
  login: (credentials: LoginCredentials) => Promise<void>
  register: (credentials: RegisterCredentials) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => authStorage.getUser())

  useEffect(() => {
    function handleUnauthorized() {
      setUser(null)
    }
    window.addEventListener(AUTH_UNAUTHORIZED_EVENT, handleUnauthorized)
    return () => window.removeEventListener(AUTH_UNAUTHORIZED_EVENT, handleUnauthorized)
  }, [])

  const login = useCallback(async (credentials: LoginCredentials) => {
    const response = await loginRequest(credentials)
    authStorage.setSession(response.access_token, response.user)
    setUser(response.user)
  }, [])

  const register = useCallback(async (credentials: RegisterCredentials) => {
    const response = await registerRequest(credentials)
    authStorage.setSession(response.access_token, response.user)
    setUser(response.user)
  }, [])

  const logout = useCallback(() => {
    authStorage.clear()
    setUser(null)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: user !== null,
      login,
      register,
      logout,
    }),
    [user, login, register, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

/** Re-exported for convenience so login/register pages can import both
 * useAuth and the error-message helper from one place. */
export { getApiErrorMessage }
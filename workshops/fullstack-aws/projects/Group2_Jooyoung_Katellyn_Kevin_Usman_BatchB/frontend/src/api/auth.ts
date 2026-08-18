import { apiClient, setAccessToken } from './client'
import type { TokenResponse, User } from '../types'

export async function login(email: string, password: string): Promise<string> {
  const { data } = await apiClient.post<TokenResponse>('/api/v1/auth/login', {
    email,
    password,
  })
  setAccessToken(data.access_token)
  return data.access_token
}

export async function fetchCurrentUser(): Promise<User> {
  const { data } = await apiClient.get<User>('/api/v1/auth/me')
  return data
}

export function logout(): void {
  setAccessToken(null)
}

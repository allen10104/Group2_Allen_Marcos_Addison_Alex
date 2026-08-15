/**
 * HTTP client for the frontend to communicate with the backend API.
 */

import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";
import type { User } from "../types/auth";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const ACCESS_TOKEN_KEY = "access_token";
const USER_KEY = "user";

export const AUTH_UNAUTHORIZED_EVENT = "auth:unauthorized";

export const authStorage = {
  getAccessToken(): string | null {
    return localStorage.getItem(ACCESS_TOKEN_KEY)
  },
  getUser(): User | null {
    const raw = localStorage.getItem(USER_KEY)
    if (!raw) return null
    try {
      return JSON.parse(raw) as User
    } catch {
      // Corrupted/old-shape value -- treat as no session rather than throw.
      return null
    }
  },
  setSession(accessToken: string, user: User) {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
    localStorage.setItem(USER_KEY, JSON.stringify(user))
  },
  clear() {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  },
}

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
})

apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = authStorage.getAccessToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error: AxiosError) => {
    return Promise.reject(error)
  }
)

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Emit a custom event to notify the app about unauthorized access.
      const event = new CustomEvent(AUTH_UNAUTHORIZED_EVENT)
      window.dispatchEvent(event)
    }
    return Promise.reject(error)
  },
)

export function getApiErrorMessage(error: unknown, fallback = "An error occurred"): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as
      | { detail?: string | { msg: string }[] }
      | undefined
    if (typeof data?.detail === 'string') {
      return data.detail
    }
    if (Array.isArray(data?.detail) && data.detail[0]?.msg) {
      return data.detail[0].msg
    }
  }
  return fallback
}
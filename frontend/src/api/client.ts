// Copyright (c) 2026 PotterWhite
// MIT License — see LICENSE in the project root.
//
// Axios client configured for JWT Bearer authentication (Phase 5.7).
//
// Token storage:
//   localStorage key 'synapse_access_token'  — short-lived (60 min)
//   localStorage key 'synapse_refresh_token' — long-lived (7 days), rotated on use
//
// Auto-refresh flow:
//   On any 401 response, attempt one refresh cycle.
//   If refresh succeeds, retry the original request with the new access token.
//   If refresh fails (expired/blacklisted), dispatch a custom 'synapse:session-expired'
//   event so the router/auth store can redirect to /login.

import axios from 'axios'
import type { AxiosInstance, AxiosError, InternalAxiosRequestConfig, AxiosResponse } from 'axios'
import type { ApiError } from '@/types/api'

export const ACCESS_TOKEN_KEY = 'synapse_access_token'
export const REFRESH_TOKEN_KEY = 'synapse_refresh_token'

// Base URL is empty: in dev, Vite proxies /api/* to Django (localhost:8000).
// In production, Nginx serves both frontend and /api/* from the same origin.
const client: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
  // Keep withCredentials for /admin/ Django admin session compatibility
  withCredentials: true,
})

// Track whether a token refresh is currently in progress to avoid parallel calls
let isRefreshing = false
let refreshSubscribers: Array<(token: string) => void> = []

function onTokenRefreshed(token: string) {
  refreshSubscribers.forEach(cb => cb(token))
  refreshSubscribers = []
}

function addRefreshSubscriber(cb: (token: string) => void) {
  refreshSubscribers.push(cb)
}

// --- Request interceptor ---
// Attach JWT Bearer token from localStorage to every outbound request.
client.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem(ACCESS_TOKEN_KEY)
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`
  }
  return config
})

// --- Response interceptor ---
// On 401: attempt token refresh once, then retry the original request.
// On persistent 401 (refresh also failed): fire session-expired event.
client.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError<ApiError>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    // Only attempt refresh on 401 and if we haven't already retried this request
    if (error.response?.status === 401 && !originalRequest._retry) {
      const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)

      // No refresh token → go straight to login
      if (!refreshToken) {
        window.dispatchEvent(new CustomEvent('synapse:session-expired'))
        return Promise.reject(new Error('Session expired. Please log in again.'))
      }

      if (isRefreshing) {
        // Another request is already refreshing — queue this one and resolve when done
        return new Promise<AxiosResponse>((resolve) => {
          addRefreshSubscriber((newToken: string) => {
            originalRequest.headers['Authorization'] = `Bearer ${newToken}`
            resolve(client(originalRequest))
          })
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const response = await axios.post('/api/auth/refresh/', { refresh: refreshToken })
        const { access, refresh } = response.data

        localStorage.setItem(ACCESS_TOKEN_KEY, access)
        if (refresh) {
          // ROTATE_REFRESH_TOKENS=True: server issues a new refresh token each time
          localStorage.setItem(REFRESH_TOKEN_KEY, refresh)
        }

        onTokenRefreshed(access)
        isRefreshing = false

        // Retry the original request with the fresh access token
        originalRequest.headers['Authorization'] = `Bearer ${access}`
        return client(originalRequest)
      } catch {
        isRefreshing = false
        refreshSubscribers = []
        localStorage.removeItem(ACCESS_TOKEN_KEY)
        localStorage.removeItem(REFRESH_TOKEN_KEY)
        window.dispatchEvent(new CustomEvent('synapse:session-expired'))
        return Promise.reject(new Error('Session expired. Please log in again.'))
      }
    }

    // All other errors: normalise to a consistent Error message
    const message =
      error.response?.data?.detail ??
      (error.response ? `HTTP ${error.response.status}` : 'Network error')
    return Promise.reject(new Error(message))
  },
)

export default client

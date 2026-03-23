import axios from 'axios'
import type { AxiosInstance, AxiosError, InternalAxiosRequestConfig, AxiosResponse } from 'axios'
import type { ApiError } from '@/types/api'

// Base URL is empty: in dev, Vite proxies /api/* to Django (localhost:8000).
// In production, Nginx serves both frontend and /api/* from the same origin.
const client: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
  // Send session cookies with every request (Django session auth)
  withCredentials: true,
})

// --- Request interceptor ---
// Attach the CSRF token required by Django for unsafe methods (POST/PUT/PATCH/DELETE).
// Django sets the 'csrftoken' cookie; we read it here and forward it as a header.
client.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const csrfToken = getCookie('csrftoken')
  if (csrfToken) {
    config.headers['X-CSRFToken'] = csrfToken
  }
  return config
})

// --- Response interceptor ---
// Normalise errors so callers always get a consistent message string.
client.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError<ApiError>) => {
    const message =
      error.response?.data?.detail ??
      (error.response ? `HTTP ${error.response.status}` : 'Network error')
    return Promise.reject(new Error(message))
  },
)

// Helper: read a browser cookie by name
function getCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'))
  return match ? decodeURIComponent(match[1]) : null
}

export default client

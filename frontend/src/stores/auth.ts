// Copyright (c) 2026 PotterWhite
// MIT License — see LICENSE in the project root.
//
// Authentication store (Phase 5.7 — JWT-based).
//
// Responsibilities:
//   - Store JWT tokens in localStorage (ACCESS_TOKEN_KEY / REFRESH_TOKEN_KEY)
//   - Expose current user, role, computed helpers (isAdmin, isEditor)
//   - login() / logout() / fetchCurrentUser() actions
//   - Listen for 'synapse:session-expired' events to clear state

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import { ACCESS_TOKEN_KEY, REFRESH_TOKEN_KEY } from '@/api/client'
import type { User } from '@/types/auth'

export const useAuthStore = defineStore('auth', () => {
  // ── State ──────────────────────────────────────────────────────────────────
  const user = ref<User | null>(null)
  const isAuthenticated = ref(false)

  // ── Computed ───────────────────────────────────────────────────────────────
  const isAdmin = computed(() =>
    user.value?.role === 'admin' || user.value?.is_superuser === true
  )
  const isEditor = computed(() =>
    isAdmin.value || user.value?.role === 'editor'
  )

  // ── Actions ────────────────────────────────────────────────────────────────

  /**
   * Attempt to log in with username + password.
   * On success: stores tokens and user profile.
   * On failure: throws Error (let the caller show the message).
   */
  async function login(username: string, password: string): Promise<void> {
    const response = await authApi.login({ username, password })
    const { access, refresh, user: userData } = response.data
    localStorage.setItem(ACCESS_TOKEN_KEY, access)
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh)
    user.value = userData
    isAuthenticated.value = true
  }

  /**
   * Log out: blacklist the refresh token on the server, clear local state.
   */
  async function logout(): Promise<void> {
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
    if (refreshToken) {
      try {
        await authApi.logout(refreshToken)
      } catch {
        // Ignore server errors during logout — clear local state regardless
      }
    }
    clearAuth()
  }

  /**
   * Fetch the current user using the stored access token.
   * Called once on app boot by the router guard.
   * Returns true if authenticated, false otherwise.
   */
  async function fetchCurrentUser(): Promise<boolean> {
    const token = localStorage.getItem(ACCESS_TOKEN_KEY)
    if (!token) {
      return false
    }
    try {
      const response = await authApi.me()
      user.value = response.data
      isAuthenticated.value = true
      return true
    } catch {
      // Token is invalid or expired and refresh also failed (interceptor cleared tokens)
      clearAuth()
      return false
    }
  }

  /**
   * Clear all auth state (called on logout or session expiry).
   */
  function clearAuth(): void {
    user.value = null
    isAuthenticated.value = false
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  }

  // Listen for the 'synapse:session-expired' custom event fired by the Axios
  // interceptor when both access and refresh tokens are exhausted.
  window.addEventListener('synapse:session-expired', () => clearAuth())

  return {
    user,
    isAuthenticated,
    isAdmin,
    isEditor,
    login,
    logout,
    fetchCurrentUser,
    clearAuth,
  }
})

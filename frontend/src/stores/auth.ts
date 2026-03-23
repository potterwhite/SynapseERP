import { defineStore } from 'pinia'
import { ref } from 'vue'
import client from '@/api/client'

interface User {
  id: number
  username: string
  email: string
}

// Authentication state. Currently uses Django session auth.
// JWT support is reserved for Phase 6 (multi-user).
export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const isAuthenticated = ref(false)

  // Fetch the currently logged-in user from Django session.
  // Called once on app mount; silently ignored if not logged in.
  async function fetchCurrentUser() {
    try {
      const response = await client.get<User>('/auth/me/')
      user.value = response.data
      isAuthenticated.value = true
    } catch {
      user.value = null
      isAuthenticated.value = false
    }
  }

  function clearAuth() {
    user.value = null
    isAuthenticated.value = false
  }

  return { user, isAuthenticated, fetchCurrentUser, clearAuth }
})

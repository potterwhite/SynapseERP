import { defineStore } from 'pinia'
import { ref } from 'vue'
import client from '@/api/client'

interface HealthResponse {
  status: string
  version: string
  pm_backend: 'vault' | 'database'
  vault_connected?: boolean
}

// Global app-level state: sidebar, theme, and PM backend mode.
export const useAppStore = defineStore('app', () => {
  const sidebarCollapsed = ref(false)

  // 'light' | 'dark' — wired into NConfigProvider
  const theme = ref<'light' | 'dark'>('light')

  // Mirrors backend SYNAPSE_PM_BACKEND setting; fetched from /api/health/
  const pmBackend = ref<'vault' | 'database'>('database')
  const vaultConnected = ref(false)

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function toggleTheme() {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
  }

  // Fetch server capabilities on app boot
  async function fetchHealth() {
    try {
      const { data } = await client.get<HealthResponse>('/health/')
      pmBackend.value = data.pm_backend ?? 'database'
      vaultConnected.value = data.vault_connected ?? false
    } catch {
      // Non-critical; defaults remain
    }
  }

  return {
    sidebarCollapsed, theme, pmBackend, vaultConnected,
    toggleSidebar, toggleTheme, fetchHealth,
  }
})

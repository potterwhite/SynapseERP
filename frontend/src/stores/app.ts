import { defineStore } from 'pinia'
import { ref } from 'vue'

// Global app-level state: sidebar, theme, and PM backend mode.
export const useAppStore = defineStore('app', () => {
  const sidebarCollapsed = ref(false)

  // 'light' | 'dark' — will wire into NConfigProvider in a later step
  const theme = ref<'light' | 'dark'>('light')

  // Mirrors backend SYNAPSE_PM_BACKEND setting; fetched from /api/health/ later
  const pmBackend = ref<'vault' | 'database'>('database')

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function toggleTheme() {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
  }

  return { sidebarCollapsed, theme, pmBackend, toggleSidebar, toggleTheme }
})

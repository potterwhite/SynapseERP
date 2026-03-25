// Copyright (c) 2026 PotterWhite
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

import { defineStore } from 'pinia'
import { ref } from 'vue'
import client from '@/api/client'

interface HealthResponse {
  status: string
  version: string
  pm_backend: 'vault' | 'database'
  vault_connected?: boolean
}

const THEME_KEY = 'synapse_theme'

// Global app-level state: sidebar, theme, and PM backend mode.
export const useAppStore = defineStore('app', () => {
  const sidebarCollapsed = ref(false)

  // Restore theme from localStorage; default to 'light'
  const storedTheme = (localStorage.getItem(THEME_KEY) as 'light' | 'dark' | null) ?? 'light'
  const theme = ref<'light' | 'dark'>(storedTheme)

  // Mirrors backend SYNAPSE_PM_BACKEND setting; fetched from /api/health/
  const pmBackend = ref<'vault' | 'database'>('database')
  const vaultConnected = ref(false)

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function toggleTheme() {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
    localStorage.setItem(THEME_KEY, theme.value)
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

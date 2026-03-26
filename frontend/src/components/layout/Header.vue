<!--
Copyright (c) 2026 PotterWhite
MIT License — see LICENSE in the project root.

Top navigation bar.
Phase 5.7: Added user info (username + role badge) and logout button.
-->

<template>
  <n-layout-header bordered style="height: 64px; padding: 0 16px; display: flex; align-items: center; justify-content: space-between;">
    <n-flex align="center" gap="8">
      <!-- Hamburger menu on mobile -->
      <n-button v-if="showMenuButton" quaternary circle @click="emit('open-drawer')">
        <template #icon>
          <n-icon><MenuOutline /></n-icon>
        </template>
      </n-button>
      <span style="font-size: 18px; font-weight: 600;">SynapseERP</span>
    </n-flex>

    <n-space align="center">
      <n-text depth="3" style="font-size: 13px;">v0.9.0-alpha</n-text>

      <!-- User info: role badge + username (hidden on very small screens) -->
      <template v-if="authStore.user">
        <n-tag
          size="small"
          :type="roleTagType"
          style="cursor: default;"
        >
          {{ authStore.user.role }}
        </n-tag>
        <n-text style="font-size: 13px;">{{ authStore.user.username }}</n-text>
        <n-tooltip trigger="hover">
          <template #trigger>
            <n-button quaternary circle size="small" @click="handleLogout" :loading="loggingOut">
              <template #icon>
                <n-icon><LogOutOutline /></n-icon>
              </template>
            </n-button>
          </template>
          Logout
        </n-tooltip>
      </template>

      <!-- Theme toggle -->
      <n-tooltip trigger="hover">
        <template #trigger>
          <n-button quaternary circle @click="appStore.toggleTheme">
            <template #icon>
              <n-icon><component :is="appStore.theme === 'dark' ? SunnyOutline : MoonOutline" /></n-icon>
            </template>
          </n-button>
        </template>
        {{ appStore.theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode' }}
      </n-tooltip>
    </n-space>
  </n-layout-header>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { NLayoutHeader, NSpace, NText, NButton, NIcon, NTooltip, NFlex, NTag } from 'naive-ui'
import { MoonOutline, SunnyOutline, MenuOutline, LogOutOutline } from '@vicons/ionicons5'
import { useAppStore } from '@/stores/app'
import { useAuthStore } from '@/stores/auth'

defineProps<{ showMenuButton?: boolean }>()
const emit = defineEmits<{
  (e: 'toggle-sidebar'): void
  (e: 'open-drawer'): void
}>()

const appStore = useAppStore()
const authStore = useAuthStore()
const router = useRouter()
const loggingOut = ref(false)

// Colour-code the role badge: admin=error(red), editor=warning(orange), viewer=default
const roleTagType = computed(() => {
  switch (authStore.user?.role) {
    case 'admin': return 'error' as const
    case 'editor': return 'warning' as const
    default: return 'default' as const
  }
})

async function handleLogout() {
  loggingOut.value = true
  try {
    await authStore.logout()
  } finally {
    loggingOut.value = false
  }
  router.push({ name: 'login' })
}
</script>

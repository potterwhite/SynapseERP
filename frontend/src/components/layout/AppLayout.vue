<template>
  <n-config-provider :theme="theme">
    <n-message-provider>
      <n-notification-provider>
        <n-dialog-provider>
          <n-layout style="height: 100vh">
            <n-layout has-sider style="height: 100%">
              <!-- Sidebar -->
              <n-layout-sider
                bordered
                collapse-mode="width"
                :collapsed-width="64"
                :width="220"
                :collapsed="sidebarCollapsed"
                show-trigger
                @collapse="sidebarCollapsed = true"
                @expand="sidebarCollapsed = false"
              >
                <AppSidebar :collapsed="sidebarCollapsed" />
              </n-layout-sider>

              <!-- Main content area -->
              <n-layout>
                <AppHeader @toggle-sidebar="sidebarCollapsed = !sidebarCollapsed" />
                <n-layout-content
                  content-style="padding: 24px; min-height: calc(100vh - 64px);"
                >
                  <router-view />
                </n-layout-content>
              </n-layout>
            </n-layout>
          </n-layout>
        </n-dialog-provider>
      </n-notification-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import {
  NConfigProvider,
  NDialogProvider,
  NLayout,
  NLayoutSider,
  NLayoutContent,
  NMessageProvider,
  NNotificationProvider,
} from 'naive-ui'
import type { GlobalTheme } from 'naive-ui'
import AppSidebar from './Sidebar.vue'
import AppHeader from './Header.vue'

// Sidebar collapsed state — shared between Header toggle button and sider trigger
const sidebarCollapsed = ref(false)

// Theme: null = light (Naive UI default), darkTheme = dark
// Will be driven by a Pinia store in Step 1.2
const theme = ref<GlobalTheme | null>(null)
</script>

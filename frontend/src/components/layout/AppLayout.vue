<!--
Copyright (c) 2026 PotterWhite

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
-->

<template>
  <n-config-provider :theme="naiveTheme">
    <n-message-provider>
      <n-notification-provider>
        <n-dialog-provider>
          <n-layout style="height: 100vh">
            <n-layout has-sider style="height: 100%">

              <!-- Desktop sidebar (hidden on mobile) -->
              <n-layout-sider
                v-if="!isMobile"
                bordered
                collapse-mode="width"
                :collapsed-width="64"
                :width="220"
                :collapsed="appStore.sidebarCollapsed"
                show-trigger
                @collapse="appStore.sidebarCollapsed = true"
                @expand="appStore.sidebarCollapsed = false"
              >
                <AppSidebar :collapsed="appStore.sidebarCollapsed" />
              </n-layout-sider>

              <!-- Main content area -->
              <n-layout>
                <AppHeader
                  :show-menu-button="isMobile"
                  @toggle-sidebar="appStore.toggleSidebar"
                  @open-drawer="drawerOpen = true"
                />
                <n-layout-content
                  :content-style="isMobile
                    ? 'padding: 16px; min-height: calc(100vh - 64px);'
                    : 'padding: 24px; min-height: calc(100vh - 64px);'"
                >
                  <router-view />
                </n-layout-content>
              </n-layout>

            </n-layout>
          </n-layout>

          <!-- Mobile nav drawer -->
          <n-drawer
            v-model:show="drawerOpen"
            :width="240"
            placement="left"
          >
            <AppSidebar :collapsed="false" @navigate="drawerOpen = false" />
          </n-drawer>

        </n-dialog-provider>
      </n-notification-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  NConfigProvider,
  NDialogProvider,
  NDrawer,
  NLayout,
  NLayoutSider,
  NLayoutContent,
  NMessageProvider,
  NNotificationProvider,
  darkTheme,
} from 'naive-ui'
import AppSidebar from './Sidebar.vue'
import AppHeader from './Header.vue'
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()

// Map string theme to Naive UI theme object: null = light default, darkTheme = dark
const naiveTheme = computed(() => appStore.theme === 'dark' ? darkTheme : null)

// ─── Responsive breakpoint ────────────────────────────────────────────────────
const MOBILE_BREAKPOINT = 768

const windowWidth = ref(window.innerWidth)
const isMobile = computed(() => windowWidth.value < MOBILE_BREAKPOINT)

function onResize() {
  windowWidth.value = window.innerWidth
}

onMounted(() => window.addEventListener('resize', onResize))
onUnmounted(() => window.removeEventListener('resize', onResize))

// Mobile drawer open state
const drawerOpen = ref(false)
</script>


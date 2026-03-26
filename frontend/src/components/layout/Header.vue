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
      <!-- NTooltip requires the trigger element in the #trigger slot -->
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
import { NLayoutHeader, NSpace, NText, NButton, NIcon, NTooltip, NFlex } from 'naive-ui'
import { MoonOutline, SunnyOutline, MenuOutline } from '@vicons/ionicons5'
import { useAppStore } from '@/stores/app'

defineProps<{ showMenuButton?: boolean }>()
const emit = defineEmits<{
  (e: 'toggle-sidebar'): void
  (e: 'open-drawer'): void
}>()

const appStore = useAppStore()
</script>

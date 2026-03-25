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
  <div style="display: flex; flex-direction: column; height: 100%;">
    <!-- Logo / app name -->
    <div class="sidebar-logo" :class="{ collapsed }">
      <n-icon :component="GridIcon" size="22" color="#18a058" />
      <span v-if="!collapsed" class="logo-text">SynapseERP</span>
    </div>

    <n-divider style="margin: 0;" />

    <n-menu
      :collapsed="collapsed"
      :collapsed-width="64"
      :collapsed-icon-size="22"
      :options="menuOptions"
      :value="activeKey"
      @update:value="handleMenuSelect"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, h } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { NMenu, NIcon, NDivider } from 'naive-ui'
import type { MenuOption } from 'naive-ui'
import {
  GridOutline as GridIcon,
  HomeOutline as DashboardIcon,
  FolderOutline as PMIcon,
  BarChartOutline as GanttIcon,
  TimeOutline as AttendanceIcon,
  DocumentTextOutline as BOMIcon,
} from '@vicons/ionicons5'

defineProps<{ collapsed: boolean }>()

const router = useRouter()
const route = useRoute()

const activeKey = computed(() => {
  const path = route.path
  if (path.startsWith('/pm/gantt')) return 'pm-gantt'
  if (path.startsWith('/pm')) return 'pm-projects'
  if (path.startsWith('/attendance')) return 'attendance'
  if (path.startsWith('/bom')) return 'bom'
  return 'dashboard'
})

function renderIcon(icon: unknown) {
  return () => h(NIcon, null, { default: () => h(icon as never) })
}

const menuOptions: MenuOption[] = [
  {
    label: 'Dashboard',
    key: 'dashboard',
    icon: renderIcon(DashboardIcon),
  },
  {
    label: 'Project Management',
    key: 'pm',
    icon: renderIcon(PMIcon),
    children: [
      {
        label: 'Projects',
        key: 'pm-projects',
      },
      {
        label: 'Gantt Chart',
        key: 'pm-gantt',
        icon: renderIcon(GanttIcon),
      },
    ],
  },
  {
    label: 'Attendance',
    key: 'attendance',
    icon: renderIcon(AttendanceIcon),
  },
  {
    label: 'BOM Analyzer',
    key: 'bom',
    icon: renderIcon(BOMIcon),
  },
]

const routeMap: Record<string, string> = {
  dashboard: '/',
  'pm-projects': '/pm',
  'pm-gantt': '/pm/gantt',
  attendance: '/attendance',
  bom: '/bom',
}

function handleMenuSelect(key: string) {
  const path = routeMap[key]
  if (path) router.push(path)
}
</script>

<style scoped>
.sidebar-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px 20px;
  height: 64px;
  overflow: hidden;
  white-space: nowrap;
}

.sidebar-logo.collapsed {
  justify-content: center;
  padding: 16px 0;
}

.logo-text {
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: var(--n-text-color);
}
</style>

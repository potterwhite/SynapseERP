<template>
  <n-menu
    :collapsed="collapsed"
    :collapsed-width="64"
    :collapsed-icon-size="22"
    :options="menuOptions"
    :value="activeKey"
    @update:value="handleMenuSelect"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { NMenu } from 'naive-ui'
import type { MenuOption } from 'naive-ui'

defineProps<{ collapsed: boolean }>()

const router = useRouter()
const route = useRoute()

// Active menu key is derived from current route path
const activeKey = computed(() => {
  const path = route.path
  if (path.startsWith('/pm/gantt')) return 'pm-gantt'
  if (path.startsWith('/pm')) return 'pm-projects'
  if (path.startsWith('/attendance')) return 'attendance'
  if (path.startsWith('/bom')) return 'bom'
  return 'dashboard'
})

const menuOptions: MenuOption[] = [
  {
    label: 'Dashboard',
    key: 'dashboard',
  },
  {
    label: 'Project Management',
    key: 'pm',
    children: [
      { label: 'Projects', key: 'pm-projects' },
      { label: 'Gantt Chart', key: 'pm-gantt' },
    ],
  },
  {
    label: 'Attendance Analyzer',
    key: 'attendance',
  },
  {
    label: 'BOM Analyzer',
    key: 'bom',
  },
]

const routeMap: Record<string, string> = {
  'dashboard': '/',
  'pm-projects': '/pm',
  'pm-gantt': '/pm/gantt',
  'attendance': '/attendance',
  'bom': '/bom',
}

function handleMenuSelect(key: string) {
  const path = routeMap[key]
  if (path) router.push(path)
}
</script>

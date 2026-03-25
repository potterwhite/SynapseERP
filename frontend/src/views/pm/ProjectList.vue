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
  <div>
    <!-- Header row: title + actions -->
    <n-flex justify="space-between" align="center" style="margin-bottom: 20px;">
      <n-h2 style="margin: 0;">Project Management</n-h2>
      <n-flex :wrap="false" gap="8">
        <n-input
          v-model:value="searchQuery"
          placeholder="Search projects…"
          clearable
          style="width: 200px;"
          @update:value="onSearch"
        >
          <template #prefix>
            <n-icon :component="SearchIcon" />
          </template>
        </n-input>
        <n-select
          v-model:value="statusFilter"
          :options="statusOptions"
          style="width: 130px;"
          @update:value="onStatusChange"
        />
        <n-button
          v-if="pmBackend === 'vault'"
          :loading="store.syncing"
          type="primary"
          ghost
          @click="handleSync"
        >
          <template #icon><n-icon :component="SyncIcon" /></template>
          Sync Vault
        </n-button>
      </n-flex>
    </n-flex>

    <!-- Stats bar -->
    <n-grid v-if="store.stats" :cols="4" :x-gap="16" style="margin-bottom: 24px;">
      <n-gi>
        <n-statistic label="Total Projects" :value="store.stats.total_projects" />
      </n-gi>
      <n-gi>
        <n-statistic label="Active" :value="store.stats.active_projects" />
      </n-gi>
      <n-gi>
        <n-statistic label="Total Tasks" :value="store.stats.total_tasks" />
      </n-gi>
      <n-gi>
        <n-statistic label="Hours Logged" :value="store.stats.total_hours_logged" />
      </n-gi>
    </n-grid>

    <!-- Error -->
    <n-result
      v-if="store.projectsError"
      status="error"
      title="Failed to load projects"
      :description="store.projectsError"
      style="padding: 48px 0;"
    />

    <!-- Project table -->
    <n-data-table
      v-else
      :columns="columns"
      :data="store.projects"
      :loading="store.projectsLoading"
      :pagination="pagination"
      :row-props="rowProps"
      :row-class-name="rowClassName"
      striped
      style="cursor: pointer;"
    />

    <!-- Task detail drawer -->
    <n-drawer
      v-model:show="drawerOpen"
      :width="560"
      placement="right"
    >
      <n-drawer-content :title="store.selectedTask?.name ?? 'Task Detail'" closable>
        <TaskDetail v-if="store.selectedTask" :task="store.selectedTask" />
        <n-spin v-else-if="store.selectedTaskLoading" style="display:flex;justify-content:center;padding:48px;" />
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, h, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  NButton, NDataTable, NDrawer, NDrawerContent, NFlex, NGrid, NGi,
  NH2, NIcon, NInput, NResult, NSelect, NSpin, NStatistic,
  NTag, NProgress, NTooltip,
  useMessage,
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { SearchOutline as SearchIcon, RefreshOutline as SyncIcon } from '@vicons/ionicons5'
import { usePmStore } from '@/stores/pm'
import { useAppStore } from '@/stores/app'
import type { Project } from '@/types/pm'
import TaskDetail from './TaskDetail.vue'

const store = usePmStore()
const appStore = useAppStore()
const router = useRouter()
const message = useMessage()

const searchQuery = ref('')
const statusFilter = ref<'active' | 'archived' | 'on_hold' | 'all'>('active')
const drawerOpen = ref(false)

const pmBackend = computed(() => appStore.pmBackend)

const statusOptions = [
  { label: 'Active', value: 'active' },
  { label: 'Archived', value: 'archived' },
  { label: 'On Hold', value: 'on_hold' },
  { label: 'All', value: 'all' },
]

const pagination = computed(() => ({
  pageSize: 20,
  showSizePicker: false,
  itemCount: store.projectsTotal,
}))

// --- Table columns ---
const columns: DataTableColumns<Project> = [
  {
    title: 'Project',
    key: 'name',
    sorter: 'default',
    render(row) {
      return h('div', [
        h('div', { style: 'font-weight: 500;' }, row.name),
        h('div', { style: 'font-size: 12px; color: var(--n-text-color-3);' }, row.full_name),
      ])
    },
  },
  {
    title: 'Status',
    key: 'status',
    width: 110,
    render(row) {
      const typeMap: Record<string, 'success' | 'warning' | 'default'> = {
        active: 'success',
        on_hold: 'warning',
        archived: 'default',
      }
      return h(NTag, { type: typeMap[row.status] ?? 'default', size: 'small', bordered: false }, {
        default: () => row.status.replace('_', ' '),
      })
    },
  },
  {
    title: 'Tasks',
    key: 'task_stats',
    width: 180,
    render(row) {
      const stats = row.task_stats
      if (!stats || stats.total === 0) {
        return h('span', { style: 'color: var(--n-text-color-3);' }, '—')
      }
      const pct = Math.round(stats.completion_rate * 100)
      return h('div', [
        h(NProgress, {
          type: 'line',
          percentage: pct,
          indicator_placement: 'outside',
          height: 8,
          color: pct === 100 ? '#18a058' : undefined,
          style: 'margin-bottom: 2px;',
        }),
        h('div', { style: 'font-size: 11px; color: var(--n-text-color-3);' },
          `${stats.done}/${stats.total} done`),
      ])
    },
  },
  {
    title: 'Hours',
    key: 'total_hours',
    width: 90,
    sorter: (a, b) => a.total_hours - b.total_hours,
    render(row) {
      return h('span', row.total_hours > 0 ? `${row.total_hours}h` : '—')
    },
  },
  {
    title: 'Deadline',
    key: 'deadline',
    width: 110,
    sorter: (a, b) => (a.deadline ?? '').localeCompare(b.deadline ?? ''),
    render(row) {
      if (!row.deadline) return h('span', { style: 'color: var(--n-text-color-3);' }, '—')
      const overdue = new Date(row.deadline) < new Date()
      return h(NTag, {
        type: overdue ? 'error' : 'default',
        size: 'small',
        bordered: false,
      }, { default: () => row.deadline })
    },
  },
  {
    title: 'Last Sync',
    key: 'synced_at',
    width: 130,
    render(row) {
      if (!row.synced_at) return h('span', { style: 'color: var(--n-text-color-3);' }, '—')
      const d = new Date(row.synced_at)
      return h(NTooltip, null, {
        default: () => d.toLocaleString(),
        trigger: () => h('span', { style: 'font-size: 12px;' }, d.toLocaleDateString()),
      })
    },
  },
]

// Click a row → open project detail (tasks in drawer)
function rowProps(row: Project) {
  return {
    onClick: () => openProject(row),
    style: 'cursor: pointer;',
  }
}

function rowClassName(row: Project) {
  return row.status === 'archived' ? 'row-archived' : ''
}

async function openProject(row: Project) {
  await store.fetchProject(row.id)
  // Navigate to the project task view via query param so the URL is shareable
  router.push({ path: '/pm', query: { project: String(row.id) } })
}

function onSearch(val: string) {
  store.fetchProjects({ search: val, status: statusFilter.value })
}

function onStatusChange(val: typeof statusFilter.value) {
  statusFilter.value = val
  store.fetchProjects({ search: searchQuery.value, status: val })
}

async function handleSync() {
  await store.syncVault()
  if (store.lastSyncResult) {
    message.success(store.lastSyncResult)
  }
}

onMounted(async () => {
  await Promise.all([
    store.fetchProjects({ status: statusFilter.value }),
    store.fetchStats(),
  ])
})
</script>

<style scoped>
:deep(.row-archived td) {
  opacity: 0.55;
}
</style>

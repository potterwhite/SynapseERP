<template>
  <div>
    <!-- Header -->
    <n-flex justify="space-between" align="center" style="margin-bottom: 20px;">
      <n-h2 style="margin: 0;">Gantt Chart</n-h2>
      <n-flex gap="8" :wrap="false">
        <!-- Project filter -->
        <n-select
          v-model:value="selectedProjectId"
          :options="projectOptions"
          placeholder="All projects"
          clearable
          style="width: 200px;"
          @update:value="onProjectChange"
        />
        <n-button
          v-if="pmBackend === 'vault'"
          :loading="store.syncing"
          type="primary"
          ghost
          @click="handleSync"
        >
          <template #icon><n-icon :component="SyncIcon" /></template>
          Sync
        </n-button>
      </n-flex>
    </n-flex>

    <!-- Error -->
    <n-result
      v-if="loadError"
      status="error"
      title="Failed to load Gantt data"
      :description="loadError"
      style="padding: 48px 0;"
    />

    <!-- Gantt component -->
    <n-card v-else>
      <GanttChart
        :tasks="ganttTasks"
        :loading="loading"
        @task-click="onTaskClick"
        @date-change="onDateChange"
      />
    </n-card>

    <!-- Task detail drawer (click on bar) -->
    <n-drawer v-model:show="drawerOpen" :width="560" placement="right">
      <n-drawer-content :title="store.selectedTask?.name ?? 'Task Detail'" closable>
        <TaskDetail v-if="store.selectedTask" :task="store.selectedTask" />
        <n-spin
          v-else-if="store.selectedTaskLoading"
          style="display:flex;justify-content:center;padding:48px;"
        />
      </n-drawer-content>
    </n-drawer>

    <!-- Date-change confirmation dialog -->
    <n-modal v-model:show="confirmOpen" preset="dialog" title="Update Task Dates?">
      <template v-if="pendingChange">
        <n-text>
          Move <b>{{ pendingChange.task.name }}</b> to<br />
          {{ fmtDate(pendingChange.start) }} → {{ fmtDate(pendingChange.end) }}?
        </n-text>
      </template>
      <template #action>
        <n-button @click="confirmOpen = false">Cancel</n-button>
        <n-button type="primary" :loading="saving" @click="confirmDateChange">Confirm</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  NButton, NCard, NDrawer, NDrawerContent, NFlex, NH2,
  NIcon, NModal, NResult, NSelect, NSpin, NText,
  useMessage,
} from 'naive-ui'
import { RefreshOutline as SyncIcon } from '@vicons/ionicons5'
import { usePmStore } from '@/stores/pm'
import { useAppStore } from '@/stores/app'
import { pmApi } from '@/api/pm'
import type { GanttTask } from '@/types/pm'
import GanttChart from '@/components/pm/GanttChart.vue'
import TaskDetail from '@/views/pm/TaskDetail.vue'

const store = usePmStore()
const appStore = useAppStore()
const message = useMessage()

const loading = ref(false)
const loadError = ref<string | null>(null)
const ganttTasks = ref<GanttTask[]>([])
const selectedProjectId = ref<number | null>(null)
const drawerOpen = ref(false)
const confirmOpen = ref(false)
const saving = ref(false)

const pmBackend = computed(() => appStore.pmBackend)

interface PendingChange {
  task: GanttTask
  start: Date
  end: Date
}
const pendingChange = ref<PendingChange | null>(null)

// Build project options from already-loaded store (may be empty on first load)
const projectOptions = computed(() => [
  ...store.projects.map(p => ({ label: p.name, value: p.id })),
])

async function loadGantt(projectId?: number | null) {
  loading.value = true
  loadError.value = null
  try {
    const { data } = await pmApi.listGanttTasks(projectId ?? undefined)
    ganttTasks.value = data.tasks
  } catch (e) {
    loadError.value = e instanceof Error ? e.message : 'Unknown error'
  } finally {
    loading.value = false
  }
}

async function onProjectChange(val: number | null) {
  selectedProjectId.value = val
  await loadGantt(val)
}

async function onTaskClick(task: GanttTask) {
  drawerOpen.value = true
  store.clearSelectedTask()
  await store.fetchTask(task.id)
}

function onDateChange(task: GanttTask, start: Date, end: Date) {
  pendingChange.value = { task, start, end }
  confirmOpen.value = true
}

async function confirmDateChange() {
  if (!pendingChange.value) return
  saving.value = true
  const { task, end } = pendingChange.value
  try {
    await pmApi.updateTask(task.id, {
      deadline: fmtDate(end),
    })
    message.success('Task dates updated')
    await loadGantt(selectedProjectId.value)
  } catch (e) {
    message.error(e instanceof Error ? e.message : 'Update failed')
  } finally {
    saving.value = false
    confirmOpen.value = false
    pendingChange.value = null
  }
}

async function handleSync() {
  await store.syncVault()
  if (store.lastSyncResult) message.success(store.lastSyncResult)
  await loadGantt(selectedProjectId.value)
}

function fmtDate(d: Date | string): string {
  if (typeof d === 'string') return d
  return d.toISOString().slice(0, 10)
}

onMounted(async () => {
  // Ensure project list is loaded so the filter dropdown is populated
  if (!store.projects.length) await store.fetchProjects({ status: 'all' })
  await loadGantt()
})
</script>

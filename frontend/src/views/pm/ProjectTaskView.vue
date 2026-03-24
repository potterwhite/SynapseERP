<template>
  <div>
    <!-- Back to project list -->
    <n-flex align="center" gap="8" style="margin-bottom: 20px;">
      <n-button text @click="router.push('/pm')">
        <template #icon><n-icon :component="BackIcon" /></template>
        All Projects
      </n-button>
      <n-text depth="3">/</n-text>
      <n-text v-if="project">{{ project.name }}</n-text>
      <n-spin v-else-if="store.selectedProjectLoading" size="small" />
    </n-flex>

    <!-- Error display -->
    <n-result
      v-if="store.selectedProjectError || store.tasksError"
      status="error"
      title="Failed to load project data"
      :description="store.selectedProjectError || store.tasksError || 'Unknown error'"
      style="padding: 48px 0;"
    >
      <template #footer>
        <n-button @click="load">Retry</n-button>
      </template>
    </n-result>

    <template v-else>
      <!-- Project header card -->
      <n-card v-if="project" style="margin-bottom: 20px;" size="small">
        <n-flex justify="space-between" align="flex-start" :wrap="false">
          <div>
            <n-h3 style="margin: 0 0 4px;">{{ project.name }}</n-h3>
            <n-text depth="3" style="font-size: 12px;">{{ project.full_name }}</n-text>
          </div>
          <n-flex gap="16" align="center">
            <n-statistic label="Tasks" :value="project.task_stats?.total ?? 0" style="text-align: center;" />
            <n-statistic label="Done" :value="project.task_stats?.done ?? 0" style="text-align: center;" />
            <n-statistic label="Hours" :value="project.total_hours ?? 0" style="text-align: center;" />
            <n-progress
              type="circle"
              :percentage="Math.round((project.task_stats?.completion_rate ?? 0) * 100)"
              :width="56"
            />
          </n-flex>
        </n-flex>
      </n-card>

      <!-- Task filter bar -->
      <n-flex gap="8" style="margin-bottom: 16px;">
        <n-select
          v-model:value="taskStatusFilter"
          :options="taskStatusOptions"
          style="width: 140px;"
          @update:value="onTaskFilter"
        />
        <n-select
          v-model:value="taskPriorityFilter"
          :options="taskPriorityOptions"
          style="width: 120px;"
          @update:value="onTaskFilter"
        />
        <n-input
          v-model:value="taskSearch"
          placeholder="Search tasks…"
          clearable
          style="width: 200px;"
          @update:value="onTaskFilter"
        />
      </n-flex>

      <!-- Task table -->
      <n-data-table
        :columns="taskColumns"
        :data="filteredTasks"
        :loading="store.tasksLoading"
        :pagination="{ pageSize: 20 }"
        striped
        style="cursor: pointer;"
      />
    </template>

    <!-- Task detail drawer -->
    <n-drawer v-model:show="drawerOpen" :width="560" placement="right">
      <n-drawer-content :title="store.selectedTask?.name ?? 'Task Detail'" closable>
        <TaskDetail v-if="store.selectedTask" :task="store.selectedTask" />
        <n-result
          v-else-if="store.selectedTaskError"
          status="error"
          title="Failed to load task"
          :description="store.selectedTaskError"
        />
        <n-spin
          v-else-if="store.selectedTaskLoading"
          style="display:flex;justify-content:center;padding:48px;"
        />
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, h, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  NButton, NCard, NDataTable, NDrawer, NDrawerContent, NFlex, NH3,
  NIcon, NInput, NProgress, NResult, NSelect, NSpin, NStatistic, NTag, NText,
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { ArrowBackOutline as BackIcon } from '@vicons/ionicons5'
import { usePmStore } from '@/stores/pm'
import type { Task } from '@/types/pm'
import TaskDetail from './TaskDetail.vue'

const store = usePmStore()
const router = useRouter()
const route = useRoute()

const drawerOpen = ref(false)
const taskStatusFilter = ref<string>('all')
const taskPriorityFilter = ref<string>('all')
const taskSearch = ref('')

const projectId = computed(() => {
  const v = route.query.project
  return v ? Number(v) : null
})

const project = computed(() => store.selectedProject)

const taskStatusOptions = [
  { label: 'All Statuses', value: 'all' },
  { label: 'To Do', value: 'todo' },
  { label: 'In Progress', value: 'doing' },
  { label: 'Done', value: 'done' },
  { label: 'Cancelled', value: 'cancelled' },
]

const taskPriorityOptions = [
  { label: 'All Priorities', value: 'all' },
  { label: 'High', value: 'high' },
  { label: 'Medium', value: 'medium' },
  { label: 'Low', value: 'low' },
]

const filteredTasks = computed(() => {
  let tasks = store.tasks
  if (taskStatusFilter.value !== 'all') {
    tasks = tasks.filter(t => t.status === taskStatusFilter.value)
  }
  if (taskPriorityFilter.value !== 'all') {
    tasks = tasks.filter(t => t.priority === taskPriorityFilter.value)
  }
  if (taskSearch.value.trim()) {
    const q = taskSearch.value.toLowerCase()
    tasks = tasks.filter(t => t.name.toLowerCase().includes(q))
  }
  return tasks
})

// --- Columns ---
const taskColumns: DataTableColumns<Task> = [
  {
    title: 'Task',
    key: 'name',
    render(row) {
      return h('div', {
        onClick: () => openTask(row.uuid),
      }, [
        h('div', { style: 'font-weight: 500;' }, row.name),
      ])
    },
  },
  {
    title: 'Status',
    key: 'status',
    width: 120,
    render(row) {
      const typeMap: Record<string, 'default' | 'info' | 'success' | 'error'> = {
        todo: 'default', doing: 'info', done: 'success', cancelled: 'error',
      }
      const labelMap: Record<string, string> = {
        todo: 'To Do', doing: 'In Progress', done: 'Done', cancelled: 'Cancelled',
      }
      return h(NTag, { type: typeMap[row.status] ?? 'default', size: 'small', bordered: false }, {
        default: () => labelMap[row.status] ?? row.status,
      })
    },
  },
  {
    title: 'Priority',
    key: 'priority',
    width: 90,
    render(row) {
      const typeMap: Record<string, 'default' | 'warning' | 'error'> = {
        low: 'default', medium: 'warning', high: 'error',
      }
      return h(NTag, { type: typeMap[row.priority] ?? 'default', size: 'small', bordered: false }, {
        default: () => row.priority,
      })
    },
  },
  {
    title: 'Deadline',
    key: 'deadline',
    width: 110,
    sorter: (a, b) => (a.deadline ?? '').localeCompare(b.deadline ?? ''),
    render(row) {
      if (!row.deadline) return h('span', { style: 'color: var(--n-text-color-3);' }, '—')
      const overdue = new Date(row.deadline) < new Date() && row.status !== 'done'
      return h('span', { style: overdue ? 'color: #d03050;' : '' }, row.deadline)
    },
  },
  {
    title: 'Est / Actual',
    key: 'hours',
    width: 110,
    render(row) {
      const est = row.estimated_hours != null ? `${row.estimated_hours}h` : '—'
      const actual = `${row.actual_hours}h`
      const over = row.estimated_hours != null && row.actual_hours > row.estimated_hours
      return h('span', { style: over ? 'color: #d03050;' : '' }, `${est} / ${actual}`)
    },
  },
]

async function openTask(uuid: string) {
  drawerOpen.value = true
  store.clearSelectedTask()
  await store.fetchTask(uuid)
}

function onTaskFilter() {
  // Filtering is done client-side via filteredTasks computed
}

async function load() {
  if (!projectId.value) return
  await Promise.all([
    store.fetchProject(projectId.value),
    store.fetchTasks({ project: projectId.value, page_size: 200 }),
  ])
}

onMounted(load)
watch(projectId, load)
</script>

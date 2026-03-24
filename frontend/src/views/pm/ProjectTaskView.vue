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

      <!-- Task filter bar + New Task button -->
      <n-flex gap="8" style="margin-bottom: 16px;" align="center">
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
        <!-- Spacer -->
        <div style="flex: 1;" />
        <n-button type="primary" @click="openCreateModal">
          <template #icon><n-icon :component="AddIcon" /></template>
          New Task
        </n-button>
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

    <!-- Task detail drawer (read-only + edit button) -->
    <n-drawer v-model:show="drawerOpen" :width="560" placement="right">
      <n-drawer-content :title="store.selectedTask?.name ?? 'Task Detail'" closable>
        <template v-if="store.selectedTask">
          <!-- Edit bar at the top of drawer -->
          <n-flex justify="flex-end" style="margin-bottom: 12px;">
            <n-button size="small" @click="openEditModal(store.selectedTask!)">
              <template #icon><n-icon :component="EditIcon" /></template>
              Edit Task
            </n-button>
          </n-flex>
          <TaskDetail :task="store.selectedTask" />
        </template>
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

    <!-- Create / Edit Task Modal -->
    <n-modal
      v-model:show="taskModalOpen"
      :title="taskModalMode === 'create' ? 'New Task' : 'Edit Task'"
      preset="card"
      style="width: 560px;"
      :mask-closable="false"
    >
      <n-form
        ref="taskFormRef"
        :model="taskForm"
        :rules="taskFormRules"
        label-placement="left"
        label-width="120px"
        require-mark-placement="right-hanging"
      >
        <n-form-item label="Task Name" path="name">
          <n-input v-model:value="taskForm.name" placeholder="Enter task name" />
        </n-form-item>

        <n-form-item label="Status" path="status">
          <n-select v-model:value="taskForm.status" :options="taskStatusOptions.slice(1)" />
        </n-form-item>

        <n-form-item label="Priority" path="priority">
          <n-select v-model:value="taskForm.priority" :options="taskPriorityOptions.slice(1)" />
        </n-form-item>

        <n-form-item label="Deadline" path="deadline">
          <n-date-picker
            v-model:formatted-value="taskForm.deadline"
            value-format="yyyy-MM-dd"
            type="date"
            clearable
            style="width: 100%;"
          />
        </n-form-item>

        <n-form-item label="Est. Hours" path="estimated_hours">
          <n-input-number
            v-model:value="taskForm.estimated_hours"
            :min="0"
            :step="0.5"
            style="width: 100%;"
            placeholder="e.g. 8"
          />
        </n-form-item>

        <n-form-item label="Description" path="description">
          <n-input
            v-model:value="taskForm.description"
            type="textarea"
            :rows="4"
            placeholder="Task description (written to vault)"
          />
        </n-form-item>
      </n-form>

      <template #footer>
        <n-flex justify="flex-end" gap="8">
          <n-button @click="taskModalOpen = false">Cancel</n-button>
          <n-button type="primary" :loading="taskSaving" @click="submitTaskForm">
            {{ taskModalMode === 'create' ? 'Create' : 'Save' }}
          </n-button>
        </n-flex>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, h, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useMessage } from 'naive-ui'
import {
  NButton, NCard, NDataTable, NDatePicker, NDrawer, NDrawerContent, NFlex, NForm,
  NFormItem, NH3, NIcon, NInput, NInputNumber, NModal, NProgress, NResult,
  NSelect, NSpin, NStatistic, NTag, NText,
} from 'naive-ui'
import type { DataTableColumns, FormInst, FormRules } from 'naive-ui'
import { ArrowBackOutline as BackIcon, AddOutline as AddIcon, CreateOutline as EditIcon } from '@vicons/ionicons5'
import { usePmStore } from '@/stores/pm'
import type { Task } from '@/types/pm'
import TaskDetail from './TaskDetail.vue'

const store = usePmStore()
const router = useRouter()
const route = useRoute()
const message = useMessage()

// --- Drawer state ---
const drawerOpen = ref(false)

// --- Filter state ---
const taskStatusFilter = ref<string>('all')
const taskPriorityFilter = ref<string>('all')
const taskSearch = ref('')

// --- Modal state ---
const taskModalOpen = ref(false)
const taskModalMode = ref<'create' | 'edit'>('create')
const taskSaving = ref(false)
const taskFormRef = ref<FormInst | null>(null)
const editingTaskUuid = ref<string | null>(null)

const taskForm = ref({
  name: '',
  status: 'todo',
  priority: 'medium',
  deadline: null as string | null,
  estimated_hours: null as number | null,
  description: '',
})

const taskFormRules: FormRules = {
  name: [{ required: true, message: 'Task name is required', trigger: 'blur' }],
  status: [{ required: true, message: 'Status is required', trigger: 'change' }],
  priority: [{ required: true, message: 'Priority is required', trigger: 'change' }],
}

// ---

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

// --- Actions ---

async function openTask(uuid: string) {
  drawerOpen.value = true
  store.clearSelectedTask()
  await store.fetchTask(uuid)
}

function onTaskFilter() {
  // Filtering is done client-side via filteredTasks computed
}

function openCreateModal() {
  taskModalMode.value = 'create'
  editingTaskUuid.value = null
  taskForm.value = {
    name: '',
    status: 'todo',
    priority: 'medium',
    deadline: null,
    estimated_hours: null,
    description: '',
  }
  taskModalOpen.value = true
}

function openEditModal(task: Task) {
  taskModalMode.value = 'edit'
  editingTaskUuid.value = task.uuid
  taskForm.value = {
    name: task.name,
    status: task.status,
    priority: task.priority,
    deadline: task.deadline ?? null,
    estimated_hours: task.estimated_hours ?? null,
    description: '',
  }
  taskModalOpen.value = true
}

async function submitTaskForm() {
  try {
    await taskFormRef.value?.validate()
  } catch {
    return // validation failed — form shows inline errors
  }

  taskSaving.value = true
  try {
    if (taskModalMode.value === 'create') {
      if (!projectId.value) return
      await store.createTask({
        name: taskForm.value.name,
        project_id: projectId.value,
        status: taskForm.value.status,
        priority: taskForm.value.priority,
        deadline: taskForm.value.deadline || null,
        estimated_hours: taskForm.value.estimated_hours,
        description: taskForm.value.description,
      })
      message.success('Task created and written to vault')
    } else {
      if (!editingTaskUuid.value) return
      await store.updateTaskInStore(editingTaskUuid.value, {
        name: taskForm.value.name,
        status: taskForm.value.status,
        priority: taskForm.value.priority,
        deadline: taskForm.value.deadline || null,
        estimated_hours: taskForm.value.estimated_hours,
        description: taskForm.value.description,
      })
      // Refresh detail if drawer is open on this task
      if (drawerOpen.value && store.selectedTask?.uuid === editingTaskUuid.value) {
        await store.fetchTask(editingTaskUuid.value)
      }
      message.success('Task updated and written to vault')
    }
    taskModalOpen.value = false
  } catch (e) {
    message.error(e instanceof Error ? e.message : 'Save failed')
  } finally {
    taskSaving.value = false
  }
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

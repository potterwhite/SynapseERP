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
    <!-- Back to project list -->
    <n-flex align="center" gap="8" style="margin-bottom: 20px;">
      <n-button text @click="router.push('/pm')">
        <template #icon><n-icon :component="BackIcon" /></template>
        {{ t('tasks.all_projects') }}
      </n-button>
      <n-text depth="3">/</n-text>
      <n-text v-if="project">{{ project.name }}</n-text>
      <n-spin v-else-if="store.selectedProjectLoading" size="small" />
    </n-flex>

    <!-- Error display -->
    <n-result
      v-if="store.selectedProjectError || store.tasksError"
      status="error"
      :title="t('common.unknown_error')"
      :description="store.selectedProjectError || store.tasksError || t('common.unknown_error')"
      style="padding: 48px 0;"
    >
      <template #footer>
        <n-button @click="load">{{ t('common.retry') }}</n-button>
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
            <n-statistic :label="t('tasks.columns.task')" :value="project.task_stats?.total ?? 0" style="text-align: center;" />
            <n-statistic :label="t('tasks.status.done')" :value="project.task_stats?.done ?? 0" style="text-align: center;" />
            <n-statistic :label="t('projects.columns.hours')" :value="project.total_hours ?? 0" style="text-align: center;" />
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
          :placeholder="t('tasks.search_placeholder')"
          clearable
          style="width: 200px;"
          @update:value="onTaskFilter"
        />
        <!-- Spacer -->
        <div style="flex: 1;" />
        <!-- Bulk delete — visible when rows are selected -->
        <n-button
          v-if="checkedTaskKeys.length > 0"
          type="error"
          :loading="bulkTaskDeleting"
          @click="confirmBulkDeleteTasks"
        >
          <template #icon><n-icon :component="DeleteIcon" /></template>
          {{ t('tasks.delete_selected', { n: checkedTaskKeys.length }) }}
        </n-button>
        <n-button type="primary" @click="openCreateModal">
          <template #icon><n-icon :component="AddIcon" /></template>
          {{ t('tasks.new_task') }}
        </n-button>
      </n-flex>

      <!-- Task table -->
      <n-data-table
        :columns="taskColumns"
        :data="filteredTasks"
        :loading="store.tasksLoading"
        :pagination="{ pageSize: 20 }"
        :row-key="(row: Task) => row.uuid"
        v-model:checked-row-keys="checkedTaskKeys"
        striped
        style="cursor: pointer;"
      />
    </template>

    <!-- Task detail drawer (read-only + edit button) -->
    <n-drawer v-model:show="drawerOpen" :width="560" placement="right">
      <n-drawer-content :title="store.selectedTask?.name ?? t('tasks.edit_task')" closable>
        <template v-if="store.selectedTask">
          <!-- Edit bar at the top of drawer -->
          <n-flex justify="flex-end" style="margin-bottom: 12px;">
            <n-button size="small" @click="openEditModal(store.selectedTask!)">
              <template #icon><n-icon :component="EditIcon" /></template>
              {{ t('tasks.edit_task') }}
            </n-button>
          </n-flex>
          <TaskDetail :task="store.selectedTask" />
        </template>
        <n-result
          v-else-if="store.selectedTaskError"
          status="error"
          :title="t('common.unknown_error')"
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
      :title="taskModalMode === 'create' ? t('tasks.new_task') : t('tasks.edit_task')"
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
        <n-form-item :label="t('tasks.form.name_label')" path="name">
          <n-input v-model:value="taskForm.name" :placeholder="t('tasks.form.name_placeholder')" />
        </n-form-item>

        <n-form-item :label="t('tasks.form.status_label')" path="status">
          <n-select v-model:value="taskForm.status" :options="taskStatusOptions.slice(1)" />
        </n-form-item>

        <n-form-item :label="t('tasks.form.priority_label')" path="priority">
          <n-select v-model:value="taskForm.priority" :options="taskPriorityOptions.slice(1)" />
        </n-form-item>

        <n-form-item :label="t('tasks.form.deadline_label')" path="deadline">
          <n-date-picker
            v-model:formatted-value="taskForm.deadline"
            value-format="yyyy-MM-dd"
            type="date"
            clearable
            style="width: 100%;"
          />
        </n-form-item>

        <n-form-item :label="t('tasks.form.est_hours_label')" path="estimated_hours">
          <n-input-number
            v-model:value="taskForm.estimated_hours"
            :min="0"
            :step="0.5"
            style="width: 100%;"
            :placeholder="t('tasks.form.est_hours_placeholder')"
          />
        </n-form-item>

        <n-form-item :label="t('tasks.form.description_label')" path="description">
          <n-input
            v-model:value="taskForm.description"
            type="textarea"
            :rows="4"
            :placeholder="t('tasks.form.description_placeholder')"
          />
        </n-form-item>
      </n-form>

      <template #footer>
        <n-flex justify="flex-end" gap="8">
          <n-button @click="taskModalOpen = false">{{ t('common.cancel') }}</n-button>
          <n-button type="primary" :loading="taskSaving" @click="submitTaskForm">
            {{ taskModalMode === 'create' ? t('common.create') : t('common.save') }}
          </n-button>
        </n-flex>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, h, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useMessage, useDialog } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import {
  NButton, NCard, NDataTable, NDatePicker, NDrawer, NDrawerContent, NFlex, NForm,
  NFormItem, NH3, NIcon, NInput, NInputNumber, NModal, NProgress, NResult,
  NSelect, NSpin, NStatistic, NTag, NText,
} from 'naive-ui'
import type { DataTableColumns, DataTableRowKey, FormInst, FormRules } from 'naive-ui'
import { ArrowBackOutline as BackIcon, AddOutline as AddIcon, CreateOutline as EditIcon, TrashOutline as DeleteIcon } from '@vicons/ionicons5'
import { usePmStore } from '@/stores/pm'
import type { Task } from '@/types/pm'
import TaskDetail from './TaskDetail.vue'

const store = usePmStore()
const router = useRouter()
const route = useRoute()
const message = useMessage()
const dialog = useDialog()
const { t } = useI18n()

// --- Drawer state ---
const drawerOpen = ref(false)

// --- Filter state ---
const taskStatusFilter = ref<string>('all')
const taskPriorityFilter = ref<string>('all')
const taskSearch = ref('')

// --- Checkbox selection for bulk delete ---
const checkedTaskKeys = ref<DataTableRowKey[]>([])
const bulkTaskDeleting = ref(false)

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
  name: [{ required: true, message: t('tasks.form.name_required'), trigger: 'blur' }],
  status: [{ required: true, message: t('tasks.form.status_required'), trigger: 'change' }],
  priority: [{ required: true, message: t('tasks.form.priority_required'), trigger: 'change' }],
}

// ---

const projectId = computed(() => {
  const v = route.query.project
  return v ? Number(v) : null
})

const project = computed(() => store.selectedProject)

const taskStatusOptions = computed(() => [
  { label: t('tasks.status.all'), value: 'all' },
  { label: t('tasks.status.todo'), value: 'todo' },
  { label: t('tasks.status.doing'), value: 'doing' },
  { label: t('tasks.status.done'), value: 'done' },
  { label: t('tasks.status.cancelled'), value: 'cancelled' },
])

const taskPriorityOptions = computed(() => [
  { label: t('tasks.priority.all'), value: 'all' },
  { label: t('tasks.priority.high'), value: 'high' },
  { label: t('tasks.priority.medium'), value: 'medium' },
  { label: t('tasks.priority.low'), value: 'low' },
])

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
const taskColumns = computed<DataTableColumns<Task>>(() => [
  { type: 'selection' },
  {
    title: t('tasks.columns.task'),
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
    title: t('tasks.columns.status'),
    key: 'status',
    width: 120,
    render(row) {
      const typeMap: Record<string, 'default' | 'info' | 'success' | 'error'> = {
        todo: 'default', doing: 'info', done: 'success', cancelled: 'error',
      }
      const labelMap: Record<string, string> = {
        todo: t('tasks.status.todo'),
        doing: t('tasks.status.doing'),
        done: t('tasks.status.done'),
        cancelled: t('tasks.status.cancelled'),
      }
      return h(NTag, { type: typeMap[row.status] ?? 'default', size: 'small', bordered: false }, {
        default: () => labelMap[row.status] ?? row.status,
      })
    },
  },
  {
    title: t('tasks.columns.priority'),
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
    title: t('tasks.columns.deadline'),
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
    title: t('tasks.columns.est_actual'),
    key: 'hours',
    width: 110,
    render(row) {
      const est = row.estimated_hours != null ? `${row.estimated_hours}h` : '—'
      const actual = `${row.actual_hours}h`
      const over = row.estimated_hours != null && row.actual_hours > row.estimated_hours
      return h('span', { style: over ? 'color: #d03050;' : '' }, `${est} / ${actual}`)
    },
  },
  {
    title: '',
    key: 'actions',
    width: 80,
    render(row) {
      return h('div', {
        style: 'display:flex;gap:4px;justify-content:flex-end;',
        onClick: (e: MouseEvent) => e.stopPropagation(),
      }, [
        h(NButton, {
          size: 'small',
          quaternary: true,
          onClick: () => openEditModal(row),
        }, { icon: () => h(NIcon, { component: EditIcon }) }),
        h(NButton, {
          size: 'small',
          quaternary: true,
          type: 'error',
          onClick: () => confirmDeleteTask(row),
        }, { icon: () => h(NIcon, { component: DeleteIcon }) }),
      ])
    },
  },
])

// --- Actions ---

async function openTask(uuid: string) {
  drawerOpen.value = true
  store.clearSelectedTask()
  await store.fetchTask(uuid)
}

function onTaskFilter() {
  // Filtering is done client-side via filteredTasks computed
}

function confirmDeleteTask(task: Task) {
  dialog.warning({
    title: t('tasks.delete_confirm_title'),
    content: t('tasks.delete_confirm_content', { name: task.name }),
    positiveText: t('common.delete'),
    negativeText: t('common.cancel'),
    onPositiveClick: async () => {
      try {
        await store.deleteTask(task.uuid)
        if (drawerOpen.value && store.selectedTask?.uuid === task.uuid) {
          drawerOpen.value = false
        }
        message.success(t('tasks.delete_success', { name: task.name }))
        await load()
      } catch (err: unknown) {
        message.error(err instanceof Error ? err.message : t('common.unknown_error'))
      }
    },
  })
}

async function confirmBulkDeleteTasks() {
  const count = checkedTaskKeys.value.length
  if (!count) return
  dialog.warning({
    title: t('tasks.bulk_delete_confirm_title', { count }),
    content: t('tasks.bulk_delete_confirm_content', { count }),
    positiveText: t('tasks.delete_selected', { n: count }),
    negativeText: t('common.cancel'),
    onPositiveClick: async () => {
      bulkTaskDeleting.value = true
      try {
        await store.bulkDeleteTasks(checkedTaskKeys.value as string[])
        checkedTaskKeys.value = []
        message.success(t('tasks.bulk_delete_success', { count }))
        await load()
      } catch (err: unknown) {
        message.error(err instanceof Error ? err.message : t('common.unknown_error'))
      } finally {
        bulkTaskDeleting.value = false
      }
    },
  })
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
      message.success(t('tasks.create_success'))
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
      message.success(t('tasks.update_success'))
    }
    taskModalOpen.value = false
  } catch (e) {
    message.error(e instanceof Error ? e.message : t('common.unknown_error'))
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

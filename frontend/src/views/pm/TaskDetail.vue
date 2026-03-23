<template>
  <div class="task-detail">
    <!-- Status + Priority badges -->
    <n-flex gap="8" style="margin-bottom: 16px;">
      <n-tag :type="statusType" :bordered="false">{{ statusLabel }}</n-tag>
      <n-tag :type="priorityType" :bordered="false" size="small">{{ task.priority }}</n-tag>
    </n-flex>

    <!-- Meta grid -->
    <n-descriptions :column="2" label-placement="top" bordered size="small" style="margin-bottom: 20px;">
      <n-descriptions-item label="Project">{{ task.project.name }}</n-descriptions-item>
      <n-descriptions-item label="UUID">
        <n-text code style="font-size: 11px;">{{ task.uuid }}</n-text>
      </n-descriptions-item>
      <n-descriptions-item label="Created">{{ task.created ?? '—' }}</n-descriptions-item>
      <n-descriptions-item label="Deadline">
        <span v-if="task.deadline" :style="overdue ? 'color: #d03050;' : ''">
          {{ task.deadline }}{{ overdue ? ' ⚠ overdue' : '' }}
        </span>
        <span v-else style="color: var(--n-text-color-3);">—</span>
      </n-descriptions-item>
      <n-descriptions-item label="Estimated">
        {{ task.estimated_hours != null ? `${task.estimated_hours}h` : '—' }}
      </n-descriptions-item>
      <n-descriptions-item label="Actual">
        <n-text :type="overtimeType">{{ task.actual_hours }}h</n-text>
      </n-descriptions-item>
    </n-descriptions>

    <!-- Dependency list -->
    <template v-if="task.depends_on.length">
      <n-divider title-placement="left" style="margin: 12px 0 8px;">
        <n-text depth="3" style="font-size: 12px;">Depends On</n-text>
      </n-divider>
      <n-flex wrap gap="6" style="margin-bottom: 16px;">
        <n-tag
          v-for="dep in task.depends_on"
          :key="dep"
          size="small"
          style="font-size: 11px; font-family: monospace;"
        >
          {{ dep.slice(0, 8) }}…
        </n-tag>
      </n-flex>
    </template>

    <!-- Time log -->
    <n-divider title-placement="left" style="margin: 12px 0 8px;">
      <n-text depth="3" style="font-size: 12px;">
        Time Log ({{ task.time_entries.length }} entries · {{ task.actual_hours }}h total)
      </n-text>
    </n-divider>

    <template v-if="task.time_entries.length">
      <n-data-table
        :columns="timeColumns"
        :data="task.time_entries"
        :pagination="{ pageSize: 8 }"
        size="small"
        striped
      />
    </template>
    <n-empty v-else description="No time entries yet" size="small" style="padding: 16px 0;" />

    <!-- Vault path (collapsed by default) -->
    <template v-if="task.vault_path">
      <n-divider style="margin: 16px 0 8px;" />
      <n-collapse>
        <n-collapse-item title="Vault info" name="vault">
          <n-text code style="font-size: 11px; word-break: break-all;">{{ task.vault_path }}</n-text>
          <br />
          <n-text depth="3" style="font-size: 11px;">
            Last synced: {{ task.synced_at ? new Date(task.synced_at).toLocaleString() : '—' }}
          </n-text>
        </n-collapse-item>
      </n-collapse>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, h } from 'vue'
import {
  NCollapse, NCollapseItem, NDataTable, NDescriptions, NDescriptionsItem,
  NDivider, NEmpty, NFlex, NTag, NText,
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import type { Task, TimeEntry } from '@/types/pm'

const props = defineProps<{ task: Task }>()

const overdue = computed(() => {
  if (!props.task.deadline) return false
  return new Date(props.task.deadline) < new Date()
})

const overtimeType = computed(() => {
  if (!props.task.estimated_hours) return 'default' as const
  return props.task.actual_hours > props.task.estimated_hours ? 'error' as const : 'default' as const
})

const statusLabel = computed(() => {
  const map: Record<string, string> = {
    todo: 'To Do', doing: 'In Progress', done: 'Done', cancelled: 'Cancelled',
  }
  return map[props.task.status] ?? props.task.status
})

const statusType = computed((): 'default' | 'info' | 'success' | 'error' => {
  const map = { todo: 'default', doing: 'info', done: 'success', cancelled: 'error' } as const
  return map[props.task.status] ?? 'default'
})

const priorityType = computed((): 'default' | 'warning' | 'error' => {
  const map = { low: 'default', medium: 'warning', high: 'error' } as const
  return map[props.task.priority] ?? 'default'
})

const timeColumns: DataTableColumns<TimeEntry> = [
  {
    title: 'Date',
    key: 'date',
    width: 100,
  },
  {
    title: 'Time',
    key: 'time',
    width: 110,
    render(row) {
      if (!row.start_time && !row.end_time) return h('span', '—')
      return h('span', `${row.start_time ?? '?'} – ${row.end_time ?? '?'}`)
    },
  },
  {
    title: 'Duration',
    key: 'duration_minutes',
    width: 80,
    render(row) {
      const h_val = Math.floor(row.duration_minutes / 60)
      const m_val = row.duration_minutes % 60
      return h('span', h_val > 0 ? `${h_val}h ${m_val}m` : `${m_val}m`)
    },
  },
  {
    title: 'Description',
    key: 'description',
    ellipsis: { tooltip: true },
  },
]
</script>

<style scoped>
.task-detail {
  padding: 4px 0;
}
</style>

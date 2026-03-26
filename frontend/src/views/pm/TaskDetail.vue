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
  <div class="task-detail">
    <!-- Status + Priority badges -->
    <n-flex gap="8" style="margin-bottom: 16px;">
      <n-tag :type="statusType" :bordered="false">{{ statusLabel }}</n-tag>
      <n-tag :type="priorityType" :bordered="false" size="small">{{ task.priority }}</n-tag>
    </n-flex>

    <!-- Meta grid -->
    <n-descriptions :column="2" label-placement="top" bordered size="small" style="margin-bottom: 20px;">
      <n-descriptions-item :label="t('task_detail.project')">{{ task.project.name }}</n-descriptions-item>
      <n-descriptions-item :label="t('task_detail.uuid')">
        <n-text code style="font-size: 11px;">{{ task.uuid }}</n-text>
      </n-descriptions-item>
      <n-descriptions-item :label="t('task_detail.created')">{{ task.created ?? '—' }}</n-descriptions-item>
      <n-descriptions-item :label="t('task_detail.deadline')">
        <span v-if="task.deadline" :style="overdue ? 'color: #d03050;' : ''">
          {{ task.deadline }}{{ overdue ? t('task_detail.overdue') : '' }}
        </span>
        <span v-else style="color: var(--n-text-color-3);">—</span>
      </n-descriptions-item>
      <n-descriptions-item :label="t('task_detail.estimated')">
        {{ task.estimated_hours != null ? `${task.estimated_hours}h` : '—' }}
      </n-descriptions-item>
      <n-descriptions-item :label="t('task_detail.actual')">
        <n-text :type="overtimeType">{{ task.actual_hours }}h</n-text>
      </n-descriptions-item>
    </n-descriptions>

    <!-- Dependency list -->
    <template v-if="task.depends_on.length">
      <n-divider title-placement="left" style="margin: 12px 0 8px;">
        <n-text depth="3" style="font-size: 12px;">{{ t('task_detail.depends_on') }}</n-text>
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
        {{ t('task_detail.time_log', { count: task.time_entries.length, hours: task.actual_hours }) }}
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
    <n-empty v-else :description="t('task_detail.no_time_entries')" size="small" style="padding: 16px 0;" />

    <!-- Vault path (collapsed by default) -->
    <template v-if="task.vault_path">
      <n-divider style="margin: 16px 0 8px;" />
      <n-collapse>
        <n-collapse-item :title="t('task_detail.vault_info')" name="vault">
          <n-text code style="font-size: 11px; word-break: break-all;">{{ task.vault_path }}</n-text>
          <br />
          <n-text depth="3" style="font-size: 11px;">
            {{ t('task_detail.last_synced') }} {{ task.synced_at ? new Date(task.synced_at).toLocaleString() : '—' }}
          </n-text>
        </n-collapse-item>
      </n-collapse>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, h } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  NCollapse, NCollapseItem, NDataTable, NDescriptions, NDescriptionsItem,
  NDivider, NEmpty, NFlex, NTag, NText,
} from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import type { Task, TimeEntry } from '@/types/pm'

const props = defineProps<{ task: Task }>()
const { t } = useI18n()

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
    todo: t('task_detail.status.todo'),
    doing: t('task_detail.status.doing'),
    done: t('task_detail.status.done'),
    cancelled: t('task_detail.status.cancelled'),
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

const timeColumns = computed<DataTableColumns<TimeEntry>>(() => [
  {
    title: t('task_detail.col_date'),
    key: 'date',
    width: 100,
  },
  {
    title: t('task_detail.col_time'),
    key: 'time',
    width: 110,
    render(row) {
      if (!row.start_time && !row.end_time) return h('span', '—')
      return h('span', `${row.start_time ?? '?'} – ${row.end_time ?? '?'}`)
    },
  },
  {
    title: t('task_detail.col_duration'),
    key: 'duration_minutes',
    width: 80,
    render(row) {
      const h_val = Math.floor(row.duration_minutes / 60)
      const m_val = row.duration_minutes % 60
      return h('span', h_val > 0 ? `${h_val}h ${m_val}m` : `${m_val}m`)
    },
  },
  {
    title: t('task_detail.col_description'),
    key: 'description',
    ellipsis: { tooltip: true },
  },
])
</script>

<style scoped>
.task-detail {
  padding: 4px 0;
}
</style>

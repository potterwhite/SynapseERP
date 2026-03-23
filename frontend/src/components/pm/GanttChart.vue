<!--
  GanttChart.vue — frappe-gantt wrapper component.

  frappe-gantt v1.x renders into a <svg> inside a container div.
  It is not Vue-aware, so we manage its lifecycle manually via
  onMounted / onUnmounted / watch.
-->
<template>
  <div class="gantt-wrapper">
    <!-- Toolbar -->
    <n-flex justify="space-between" align="center" style="margin-bottom: 12px;">
      <n-flex gap="8" align="center">
        <n-text depth="3" style="font-size: 13px;">View:</n-text>
        <n-button-group>
          <n-button
            v-for="v in VIEW_MODES"
            :key="v"
            size="small"
            :type="currentView === v ? 'primary' : 'default'"
            @click="setView(v)"
          >{{ v }}</n-button>
        </n-button-group>
      </n-flex>
      <n-flex gap="8" align="center">
        <n-text v-if="tasks.length" depth="3" style="font-size: 13px;">
          {{ tasks.length }} tasks
        </n-text>
        <slot name="toolbar-extra" />
      </n-flex>
    </n-flex>

    <!-- Chart container — frappe-gantt renders here -->
    <div class="gantt-container" ref="containerRef" />

    <!-- Empty state -->
    <n-empty
      v-if="!tasks.length && !loading"
      description="No tasks to display"
      style="padding: 48px 0;"
    />
    <n-spin
      v-if="loading"
      style="display: flex; justify-content: center; padding: 48px;"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { NButton, NButtonGroup, NFlex, NEmpty, NSpin, NText } from 'naive-ui'
import Gantt from 'frappe-gantt'
// Import CSS via explicit path — frappe-gantt's package.json exports field
// does not expose the stylesheet under a standard condition, which causes
// Vite 8 (rolldown) to reject the bare specifier. Using the dist path
// directly bypasses the exports map restriction.
import '/node_modules/frappe-gantt/dist/frappe-gantt.css'
import type { GanttTask } from '@/types/pm'

const VIEW_MODES = ['Day', 'Week', 'Month'] as const
type ViewMode = (typeof VIEW_MODES)[number]

const props = withDefaults(defineProps<{
  tasks: GanttTask[]
  loading?: boolean
  initialView?: ViewMode
}>(), {
  loading: false,
  initialView: 'Week',
})

const emit = defineEmits<{
  (e: 'task-click', task: GanttTask): void
  (e: 'date-change', task: GanttTask, start: Date, end: Date): void
}>()

const containerRef = ref<HTMLElement | null>(null)
const currentView = ref<ViewMode>(props.initialView)
let ganttInstance: InstanceType<typeof Gantt> | null = null

// frappe-gantt expects tasks in its own format
function toFrappeTask(t: GanttTask) {
  return {
    id: t.id,
    name: t.name,
    start: t.start,
    end: t.end,
    progress: t.progress,
    dependencies: t.dependencies || '',
    custom_class: `bar-${t.status}`,
  }
}

function buildGantt() {
  if (!containerRef.value || !props.tasks.length) return

  // Clear previous instance
  containerRef.value.innerHTML = ''

  const frappeTasks = props.tasks.map(toFrappeTask)

  ganttInstance = new Gantt(containerRef.value, frappeTasks, {
    view_mode: currentView.value,
    date_format: 'YYYY-MM-DD',
    on_click: (fTask: { id: string }) => {
      const orig = props.tasks.find(t => t.id === fTask.id)
      if (orig) emit('task-click', orig)
    },
    on_date_change: (fTask: { id: string }, start: Date, end: Date) => {
      const orig = props.tasks.find(t => t.id === fTask.id)
      if (orig) emit('date-change', orig, start, end)
    },
  })
}

function setView(mode: ViewMode) {
  currentView.value = mode
  ganttInstance?.change_view_mode(mode)
}

onMounted(() => nextTick(buildGantt))

// Rebuild when tasks data changes
watch(() => props.tasks, () => nextTick(buildGantt), { deep: true })

onUnmounted(() => {
  ganttInstance = null
})
</script>

<style>
/* Gantt bar colour by task status — applied via custom_class */
.gantt .bar-todo .bar { fill: #94a3b8; }
.gantt .bar-doing .bar { fill: #3b82f6; }
.gantt .bar-done .bar { fill: #22c55e; }
.gantt .bar-cancelled .bar { fill: #94a3b8; opacity: 0.4; }
.gantt .bar-wrapper:hover .bar { filter: brightness(1.1); }
</style>

<style scoped>
.gantt-wrapper {
  overflow: hidden;
}
.gantt-container {
  overflow-x: auto;
  min-height: 120px;
}
</style>

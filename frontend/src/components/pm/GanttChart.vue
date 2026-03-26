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

const VIEW_MODES = ['Day', 'Week', 'Month', 'Year'] as const
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

// Debounce date-change to avoid rapid-fire dialog during drag
let dateChangeTimer: ReturnType<typeof setTimeout> | null = null

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
    // Always scroll to today on initial render so the chart shows the current
    // date region regardless of when the tasks were created.
    scroll_to: 'today',
    on_click: (fTask: { id: string }) => {
      const orig = props.tasks.find(t => t.id === fTask.id)
      if (orig) emit('task-click', orig)
    },
    on_date_change: (fTask: { id: string }, start: Date, end: Date) => {
      // Debounce: frappe-gantt fires this on every snap during drag.
      // Only emit once after the user finishes dragging (300ms idle).
      if (dateChangeTimer) clearTimeout(dateChangeTimer)
      dateChangeTimer = setTimeout(() => {
        const orig = props.tasks.find(t => t.id === fTask.id)
        if (orig) emit('date-change', orig, start, end)
        dateChangeTimer = null
      }, 300)
    },
  })
}

function setView(mode: ViewMode) {
  currentView.value = mode
  // Rebuild the entire Gantt instance so that scroll_to:'today' re-applies.
  // change_view_mode() alone does NOT re-scroll, leaving the chart stuck at
  // whatever date range was visible at initial construction.
  nextTick(buildGantt)
}

onMounted(() => nextTick(buildGantt))

// Rebuild when tasks data changes
watch(() => props.tasks, () => nextTick(buildGantt), { deep: true })

onUnmounted(() => {
  if (dateChangeTimer) clearTimeout(dateChangeTimer)
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

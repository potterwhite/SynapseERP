// Copyright (c) 2026 PotterWhite
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { pmApi } from '@/api/pm'
import type { Project, Task, PmStats } from '@/types/pm'
import type { ProjectListParams, TaskListParams, TaskCreatePayload, TaskUpdatePayload, ProjectCreatePayload, ProjectUpdatePayload } from '@/api/pm'

export const usePmStore = defineStore('pm', () => {
  // --- Projects ---
  const projects = ref<Project[]>([])
  const projectsTotal = ref(0)
  const projectsLoading = ref(false)
  const projectsError = ref<string | null>(null)

  // --- Tag filtering (Phase 5.4) ---
  /** All tags currently in use across projects */
  const allTags = ref<string[]>([])
  /** Meeting mode: when true, projects tagged 'personal' are hidden client-side */
  const meetingMode = ref(false)

  // Currently selected project (for detail / task drill-down)
  const selectedProject = ref<(Project & { tasks?: Task[] }) | null>(null)
  const selectedProjectLoading = ref(false)
  const selectedProjectError = ref<string | null>(null)

  // --- Tasks (flat list, for global task view) ---
  const tasks = ref<Task[]>([])
  const tasksTotal = ref(0)
  const tasksLoading = ref(false)
  const tasksError = ref<string | null>(null)

  // Currently selected task (detail panel)
  const selectedTask = ref<Task | null>(null)
  const selectedTaskLoading = ref(false)
  const selectedTaskError = ref<string | null>(null)

  // --- Stats ---
  const stats = ref<PmStats | null>(null)

  // --- Syncing ---
  const syncing = ref(false)
  const lastSyncResult = ref<string | null>(null)

  // --- Computed ---
  const activeProjects = computed(() =>
    projects.value.filter(p => p.status === 'active')
  )

  /**
   * Projects visible in meeting mode — hides any project tagged 'personal'.
   * Components can use this computed instead of `projects` when in meeting mode.
   */
  const visibleProjects = computed(() =>
    meetingMode.value
      ? projects.value.filter(p => !(p.tags ?? []).includes('personal'))
      : projects.value
  )

  // --- Actions ---

  async function fetchProjects(params: ProjectListParams = {}) {
    projectsLoading.value = true
    projectsError.value = null
    try {
      const { data } = await pmApi.listProjects({ status: 'all', ...params })
      projects.value = data.results
      projectsTotal.value = data.count
    } catch (e) {
      projectsError.value = e instanceof Error ? e.message : 'Failed to load projects'
    } finally {
      projectsLoading.value = false
    }
  }

  async function fetchProject(id: number) {
    selectedProjectLoading.value = true
    selectedProjectError.value = null
    try {
      const { data } = await pmApi.getProject(id)
      selectedProject.value = data
    } catch (e) {
      selectedProjectError.value = e instanceof Error ? e.message : 'Failed to load project'
    } finally {
      selectedProjectLoading.value = false
    }
  }

  async function fetchTasks(params: TaskListParams = {}) {
    tasksLoading.value = true
    tasksError.value = null
    try {
      const { data } = await pmApi.listTasks({ page_size: 100, ...params })
      tasks.value = data.results
      tasksTotal.value = data.count
    } catch (e) {
      tasksError.value = e instanceof Error ? e.message : 'Failed to load tasks'
    } finally {
      tasksLoading.value = false
    }
  }

  async function fetchTask(uuid: string) {
    selectedTaskLoading.value = true
    selectedTaskError.value = null
    try {
      const { data } = await pmApi.getTask(uuid)
      selectedTask.value = data
    } catch (e) {
      selectedTaskError.value = e instanceof Error ? e.message : 'Failed to load task'
    } finally {
      selectedTaskLoading.value = false
    }
  }

  async function fetchStats() {
    try {
      const { data } = await pmApi.getStats()
      stats.value = data
    } catch {
      // stats are non-critical — silently ignore
    }
  }

  async function fetchTags() {
    try {
      const { data } = await pmApi.listTags()
      allTags.value = data.tags
    } catch {
      // tags are non-critical — silently ignore
    }
  }

  function toggleMeetingMode() {
    meetingMode.value = !meetingMode.value
  }

  async function syncVault() {
    syncing.value = true
    lastSyncResult.value = null
    try {
      const { data } = await pmApi.syncVault()
      lastSyncResult.value = `Synced ${data.tasks_synced} tasks in ${data.duration_ms}ms`
      // Refresh project list after sync
      await fetchProjects()
    } catch (e) {
      lastSyncResult.value = e instanceof Error ? e.message : 'Sync failed'
    } finally {
      syncing.value = false
    }
  }

  function clearSelectedTask() {
    selectedTask.value = null
    selectedTaskError.value = null
  }

  async function createTask(data: TaskCreatePayload): Promise<Task> {
    const { data: task } = await pmApi.createTask(data)
    // Insert new task at the top of the list
    tasks.value = [task, ...tasks.value]
    return task
  }

  async function createProject(data: ProjectCreatePayload): Promise<Project> {
    const { data: project } = await pmApi.createProject(data)
    projects.value = [project, ...projects.value]
    projectsTotal.value += 1
    return project
  }

  async function updateProject(id: number, data: ProjectUpdatePayload): Promise<Project> {
    const { data: updated } = await pmApi.updateProject(id, data)
    const idx = projects.value.findIndex(p => p.id === id)
    if (idx !== -1) projects.value[idx] = updated
    if (selectedProject.value?.id === id) selectedProject.value = { ...selectedProject.value, ...updated }
    return updated
  }

  async function deleteProject(id: number): Promise<void> {
    await pmApi.deleteProject(id)
    projects.value = projects.value.filter(p => p.id !== id)
    projectsTotal.value = Math.max(0, projectsTotal.value - 1)
    if (selectedProject.value?.id === id) selectedProject.value = null
  }

  async function updateTaskInStore(uuid: string, data: TaskUpdatePayload): Promise<Task | null> {
    const { data: updated } = await pmApi.updateTask(uuid, data)
    // Update in flat task list
    const idx = tasks.value.findIndex(t => t.uuid === uuid)
    if (idx !== -1) tasks.value[idx] = updated
    // Update selected task if it matches
    if (selectedTask.value?.uuid === uuid) selectedTask.value = updated
    return updated
  }

  return {
    // State
    projects, projectsTotal, projectsLoading, projectsError,
    selectedProject, selectedProjectLoading, selectedProjectError,
    tasks, tasksTotal, tasksLoading, tasksError,
    selectedTask, selectedTaskLoading, selectedTaskError,
    stats, syncing, lastSyncResult,
    allTags, meetingMode,
    // Computed
    activeProjects, visibleProjects,
    // Actions
    fetchProjects, fetchProject, fetchTasks, fetchTask,
    fetchStats, fetchTags, toggleMeetingMode, syncVault, clearSelectedTask,
    createTask, updateTaskInStore,
    createProject, updateProject, deleteProject,
  }
})

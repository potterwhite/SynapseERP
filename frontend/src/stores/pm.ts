import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { pmApi } from '@/api/pm'
import type { Project, Task, PmStats } from '@/types/pm'
import type { ProjectListParams, TaskListParams } from '@/api/pm'

export const usePmStore = defineStore('pm', () => {
  // --- Projects ---
  const projects = ref<Project[]>([])
  const projectsTotal = ref(0)
  const projectsLoading = ref(false)
  const projectsError = ref<string | null>(null)

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

  return {
    // State
    projects, projectsTotal, projectsLoading, projectsError,
    selectedProject, selectedProjectLoading, selectedProjectError,
    tasks, tasksTotal, tasksLoading, tasksError,
    selectedTask, selectedTaskLoading, selectedTaskError,
    stats, syncing, lastSyncResult,
    // Computed
    activeProjects,
    // Actions
    fetchProjects, fetchProject, fetchTasks, fetchTask,
    fetchStats, syncVault, clearSelectedTask,
  }
})

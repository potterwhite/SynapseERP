// PM module API calls — all requests go through the shared Axios client.

import client from '@/api/client'
import type { PaginatedResponse } from '@/types/api'
import type { Project, Task, GanttTask, PmStats } from '@/types/pm'

export interface ProjectListParams {
  status?: 'active' | 'archived' | 'on_hold' | 'all'
  search?: string
  ordering?: string
  page?: number
  page_size?: number
}

export interface TaskListParams {
  project?: number
  status?: string
  priority?: string
  search?: string
  page?: number
  page_size?: number
}

/** Payload for creating a new task (mirrors TaskWriteSerializer) */
export interface TaskCreatePayload {
  name: string
  project_id: number
  status?: string
  priority?: string
  deadline?: string | null
  estimated_hours?: number | null
  description?: string
}

/** Payload for updating an existing task (all fields optional) */
export interface TaskUpdatePayload {
  name?: string
  status?: string
  priority?: string
  deadline?: string | null
  estimated_hours?: number | null
  description?: string
}

export const pmApi = {
  // Projects
  listProjects(params: ProjectListParams = {}) {
    return client.get<PaginatedResponse<Project>>('/pm/projects/', { params })
  },

  getProject(id: number) {
    return client.get<Project & { tasks: Task[] }>(`/pm/projects/${id}/`)
  },

  // Tasks
  listTasks(params: TaskListParams = {}) {
    return client.get<PaginatedResponse<Task>>('/pm/tasks/', { params })
  },

  getTask(uuid: string) {
    return client.get<Task>(`/pm/tasks/${uuid}/`)
  },

  createTask(data: TaskCreatePayload) {
    return client.post<Task>('/pm/tasks/', data)
  },

  updateTask(uuid: string, data: TaskUpdatePayload) {
    return client.patch<Task>(`/pm/tasks/${uuid}/`, data)
  },

  // Gantt
  listGanttTasks(projectId?: number) {
    return client.get<{ tasks: GanttTask[] }>('/pm/gantt/', {
      params: projectId ? { project: projectId } : {},
    })
  },

  // Stats
  getStats() {
    return client.get<PmStats>('/pm/stats/')
  },

  // Vault sync (vault mode only)
  syncVault() {
    return client.post<{ status: string; tasks_synced: number; duration_ms: number }>('/pm/sync/')
  },
}

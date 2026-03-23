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

  updateTask(uuid: string, data: Partial<Pick<Task, 'status' | 'priority' | 'deadline' | 'estimated_hours'>>) {
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

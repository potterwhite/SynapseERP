// PM module TypeScript types — mirror the DRF serializer shapes exactly.

export type ProjectStatus = 'active' | 'archived' | 'on_hold'
export type ParaType = 'project' | 'archive'
export type TaskStatus = 'todo' | 'doing' | 'done' | 'cancelled'
export type TaskPriority = 'low' | 'medium' | 'high'

export interface TaskStats {
  total: number
  todo: number
  doing: number
  done: number
  cancelled: number
  completion_rate: number  // 0.0 – 1.0
}

export interface Project {
  id: number
  name: string
  full_name: string
  para_type: ParaType
  status: ProjectStatus
  created: string | null
  deadline: string | null
  vault_path: string
  task_stats: TaskStats
  total_hours: number
  synced_at: string | null
}

export interface TaskSummary {
  id: number
  uuid: string
  name: string
  status: TaskStatus
  priority: TaskPriority
  created: string | null
  deadline: string | null
  estimated_hours: number | null
  actual_hours: number
}

export interface TimeEntry {
  id: number
  task_uuid: string
  date: string
  description: string
  start_time: string | null
  end_time: string | null
  duration_minutes: number
  source_note_path: string
}

export interface Task {
  id: number
  uuid: string
  name: string
  project: { id: number; name: string }
  status: TaskStatus
  priority: TaskPriority
  created: string | null
  deadline: string | null
  estimated_hours: number | null
  actual_hours: number
  depends_on: string[]   // UUIDs
  vault_path: string
  synced_at: string | null
  time_entries: TimeEntry[]
}

export interface GanttTask {
  id: string
  name: string
  start: string
  end: string
  progress: number
  dependencies: string
  project_id: number
  project_name: string
  status: TaskStatus
  priority: TaskPriority
}

export interface PmStats {
  total_projects: number
  active_projects: number
  total_tasks: number
  done_tasks: number
  doing_tasks: number
  todo_tasks: number
  total_hours_logged: number
}

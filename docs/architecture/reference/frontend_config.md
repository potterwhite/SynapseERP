# 前端配置文件精确定义

> **⚠️ SETUP REFERENCE ONLY — FOR AI AGENTS**
> This file describes the initial frontend project setup (now complete).
> The project uses `npm` (not `pnpm`) in practice.
> For current frontend file structure and patterns, see `13_codebase_map.md`.
> Only read this file if you need to understand historical project init decisions.
>
> 日期：2026-03-21
> 状态：初始化完成（历史参考）
> 用途：前端项目初始化配置记录

---

## 一、初始化命令

```bash
# 在项目根目录执行
pnpm create vite frontend -- --template vue-ts
cd frontend
pnpm install

# 核心依赖
pnpm install naive-ui @vicons/ionicons5
pnpm install vue-router@4 pinia axios
pnpm install frappe-gantt
pnpm install markdown-it
pnpm install dayjs

# 开发依赖
pnpm install -D @types/node
pnpm install -D @vitejs/plugin-vue
```

---

## 二、vite.config.ts

```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],

  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },

  server: {
    port: 5173,
    // Proxy API requests to Django backend during development
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },

  build: {
    outDir: 'dist',
    // Generate source maps for debugging
    sourcemap: true,
  },
})
```

---

## 三、tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "skipLibCheck": true,

    /* Bundler mode */
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "preserve",

    /* Linting */
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,

    /* Path aliases */
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src/**/*.ts", "src/**/*.tsx", "src/**/*.vue", "env.d.ts"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

---

## 四、src/main.ts (入口文件)

```typescript
/**
 * Synapse Frontend Application Entry Point
 *
 * This is the main entry file for the Vue 3 SPA.
 * It initializes the Vue app with all plugins: Router, Pinia, Naive UI.
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from '@/router'
import App from '@/App.vue'

// Naive UI: Import only what we need (tree-shaking)
import {
  create,
  NConfigProvider,
  NMessageProvider,
  NDialogProvider,
  NNotificationProvider,
} from 'naive-ui'

const app = createApp(App)

// Install plugins
app.use(createPinia())  // State management
app.use(router)          // Client-side routing

// Mount the app
app.mount('#app')
```

---

## 五、src/router/index.ts

```typescript
/**
 * Vue Router Configuration
 *
 * Defines all client-side routes for the Synapse SPA.
 * Uses lazy loading (dynamic imports) for code splitting.
 */
import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('@/views/Dashboard.vue'),
    meta: { title: 'Dashboard' },
  },
  {
    path: '/pm',
    component: () => import('@/views/pm/PMLayout.vue'),
    children: [
      {
        path: '',
        redirect: '/pm/projects',
      },
      {
        path: 'projects',
        component: () => import('@/views/pm/ProjectList.vue'),
        meta: { title: 'Projects' },
      },
      {
        path: 'projects/:id',
        component: () => import('@/views/pm/ProjectDetail.vue'),
        meta: { title: 'Project Detail' },
      },
      {
        path: 'tasks/:uuid',
        component: () => import('@/views/pm/TaskDetail.vue'),
        meta: { title: 'Task Detail' },
      },
      {
        path: 'gantt',
        component: () => import('@/views/pm/GanttView.vue'),
        meta: { title: 'Gantt Chart' },
      },
    ],
  },
  {
    path: '/attendance',
    component: () => import('@/views/attendance/AttendanceLayout.vue'),
    children: [
      {
        path: '',
        component: () => import('@/views/attendance/Upload.vue'),
        meta: { title: 'Attendance Analyzer' },
      },
      {
        path: 'result',
        component: () => import('@/views/attendance/Result.vue'),
        meta: { title: 'Analysis Result' },
      },
    ],
  },
  {
    path: '/bom',
    component: () => import('@/views/bom/BOMLayout.vue'),
    children: [
      {
        path: '',
        component: () => import('@/views/bom/Upload.vue'),
        meta: { title: 'BOM Analyzer' },
      },
      {
        path: 'result',
        component: () => import('@/views/bom/Result.vue'),
        meta: { title: 'BOM Result' },
      },
    ],
  },
  {
    path: '/settings',
    component: () => import('@/views/Settings.vue'),
    meta: { title: 'Settings' },
  },
  {
    path: '/login',
    component: () => import('@/views/Login.vue'),
    meta: { title: 'Login', noAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Navigation guard: redirect to login if not authenticated
router.beforeEach((to, from, next) => {
  // TODO: Check auth state from Pinia store
  next()
})

export default router
```

---

## 六、src/api/client.ts

```typescript
/**
 * Axios HTTP Client Configuration
 *
 * Centralized API client with:
 * - Base URL configuration
 * - Request/response interceptors
 * - CSRF token handling (for Django)
 * - Unified error handling
 */
import axios, { type AxiosError, type AxiosResponse } from 'axios'

// Create Axios instance with default config
const apiClient = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  // Send cookies with requests (needed for Django session auth)
  withCredentials: true,
})

/**
 * Request interceptor: Add CSRF token to mutating requests.
 * Django requires CSRF token for POST/PUT/PATCH/DELETE.
 */
apiClient.interceptors.request.use((config) => {
  // Get CSRF token from cookie (set by Django)
  const csrfToken = document.cookie
    .split('; ')
    .find((row) => row.startsWith('csrftoken='))
    ?.split('=')[1]

  if (csrfToken && config.method !== 'get') {
    config.headers['X-CSRFToken'] = csrfToken
  }

  return config
})

/**
 * Response interceptor: Handle common error patterns.
 */
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Redirect to login page
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default apiClient
```

---

## 七、src/types/pm.ts

```typescript
/**
 * TypeScript type definitions for Project Management data.
 *
 * These types mirror the API response shapes defined in
 * docs/architecture/10_API接口规格说明书.md
 */

/** Task status values */
export type TaskStatus = 'todo' | 'doing' | 'done' | 'cancelled'

/** Task priority values */
export type TaskPriority = 'low' | 'medium' | 'high'

/** PARA type classification */
export type ParaType = 'project' | 'area'

/** Task statistics for a project */
export interface TaskStats {
  total: number
  todo: number
  doing: number
  done: number
  cancelled: number
  completion_rate: number
}

/** Project summary (list view) */
export interface Project {
  id: number
  name: string
  full_name: string
  para_type: ParaType
  status: 'active' | 'archived'
  created: string          // ISO date string
  deadline: string | null
  vault_path: string
  task_stats: TaskStats
  total_hours: number
  updated_at: string       // ISO datetime string
}

/** Project detail (with tasks) */
export interface ProjectDetail extends Project {
  description: string
  tasks: TaskSummary[]
}

/** Task summary (in project context) */
export interface TaskSummary {
  id: number
  uuid: string
  name: string
  display_name: string
  status: TaskStatus
  priority: TaskPriority
  created: string
  deadline: string | null
  estimated_hours: number | null
  actual_hours: number
}

/** Full task detail */
export interface TaskDetail extends TaskSummary {
  project: { id: number; name: string }
  depends_on: string[]
  vault_path: string
  description_markdown: string
  time_entries: TimeEntry[]
}

/** Time entry record */
export interface TimeEntry {
  id: number
  date: string
  description: string
  start_time: string
  end_time: string
  duration_minutes: number
  daily_note_path: string
}

/** Gantt chart task (frappe-gantt format) */
export interface GanttTask {
  id: string
  name: string
  start: string
  end: string
  progress: number
  dependencies: string
  custom_class: string
  project_name: string
}

/** PM statistics */
export interface PMStats {
  total_projects: number
  active_projects: number
  archived_projects: number
  total_tasks: number
  tasks_by_status: Record<TaskStatus, number>
  total_hours_logged: number
  hours_this_week: number
  overdue_tasks: number
}

/** Paginated response from DRF */
export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}
```

---

## 八、src/stores/pm.ts

```typescript
/**
 * Pinia Store for Project Management state.
 *
 * Manages the client-side cache of projects, tasks, and related data.
 * All data fetching goes through this store.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import apiClient from '@/api/client'
import type {
  Project,
  ProjectDetail,
  TaskDetail,
  GanttTask,
  PMStats,
  PaginatedResponse,
  TaskStatus,
} from '@/types/pm'

export const usePMStore = defineStore('pm', () => {
  // --- State ---
  const projects = ref<Project[]>([])
  const currentProject = ref<ProjectDetail | null>(null)
  const currentTask = ref<TaskDetail | null>(null)
  const ganttTasks = ref<GanttTask[]>([])
  const stats = ref<PMStats | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // --- Getters ---
  const activeProjects = computed(() =>
    projects.value.filter((p) => p.status === 'active')
  )
  const archivedProjects = computed(() =>
    projects.value.filter((p) => p.status === 'archived')
  )

  // --- Actions ---

  /** Fetch all projects from API */
  async function fetchProjects(status: string = 'active') {
    loading.value = true
    error.value = null
    try {
      const response = await apiClient.get<PaginatedResponse<Project>>(
        '/pm/projects/',
        { params: { status, page_size: 100 } }
      )
      projects.value = response.data.results
    } catch (e: any) {
      error.value = e.response?.data?.detail || 'Failed to fetch projects'
    } finally {
      loading.value = false
    }
  }

  /** Fetch single project detail */
  async function fetchProject(id: number) {
    loading.value = true
    try {
      const response = await apiClient.get<ProjectDetail>(`/pm/projects/${id}/`)
      currentProject.value = response.data
    } catch (e: any) {
      error.value = e.response?.data?.detail || 'Failed to fetch project'
    } finally {
      loading.value = false
    }
  }

  /** Fetch single task detail */
  async function fetchTask(uuid: string) {
    loading.value = true
    try {
      const response = await apiClient.get<TaskDetail>(`/pm/tasks/${uuid}/`)
      currentTask.value = response.data
    } catch (e: any) {
      error.value = e.response?.data?.detail || 'Failed to fetch task'
    } finally {
      loading.value = false
    }
  }

  /** Fetch gantt chart data */
  async function fetchGanttData(projectId?: number) {
    loading.value = true
    try {
      const params: Record<string, any> = {}
      if (projectId) params.project = projectId
      const response = await apiClient.get<{ tasks: GanttTask[] }>(
        '/pm/gantt/',
        { params }
      )
      ganttTasks.value = response.data.tasks
    } catch (e: any) {
      error.value = e.response?.data?.detail || 'Failed to fetch gantt data'
    } finally {
      loading.value = false
    }
  }

  /** Update a task (status, deadline, etc.) */
  async function updateTask(uuid: string, data: Partial<TaskDetail>) {
    try {
      const response = await apiClient.patch<TaskDetail>(
        `/pm/tasks/${uuid}/`,
        data
      )
      currentTask.value = response.data
      // Refresh projects to update stats
      await fetchProjects()
    } catch (e: any) {
      error.value = e.response?.data?.detail || 'Failed to update task'
      throw e
    }
  }

  /** Trigger vault sync */
  async function syncVault() {
    loading.value = true
    try {
      const response = await apiClient.post('/pm/sync/')
      // Refresh all data after sync
      await fetchProjects()
      return response.data
    } catch (e: any) {
      error.value = e.response?.data?.detail || 'Sync failed'
      throw e
    } finally {
      loading.value = false
    }
  }

  return {
    // State
    projects, currentProject, currentTask, ganttTasks, stats, loading, error,
    // Getters
    activeProjects, archivedProjects,
    // Actions
    fetchProjects, fetchProject, fetchTask, fetchGanttData,
    updateTask, syncVault,
  }
})
```

---

## 九、Django DRF 序列化器模式

```python
# backend/src/synapse_pm/serializers.py

from rest_framework import serializers
from .models import Project, Task, TimeEntry


class TaskStatsSerializer(serializers.Serializer):
    """Inline serializer for task statistics."""
    total = serializers.IntegerField()
    todo = serializers.IntegerField()
    doing = serializers.IntegerField()
    done = serializers.IntegerField()
    cancelled = serializers.IntegerField()
    completion_rate = serializers.FloatField()


class ProjectListSerializer(serializers.ModelSerializer):
    """Serializer for project list view."""
    task_stats = TaskStatsSerializer(source='get_task_stats', read_only=True)
    total_hours = serializers.FloatField(source='get_total_hours', read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'full_name', 'para_type', 'status',
            'created', 'deadline', 'vault_path',
            'task_stats', 'total_hours', 'updated_at',
        ]


class TimeEntrySerializer(serializers.ModelSerializer):
    """Serializer for time entry records."""
    duration_minutes = serializers.IntegerField(read_only=True)

    class Meta:
        model = TimeEntry
        fields = [
            'id', 'date', 'description', 'start_time', 'end_time',
            'duration_minutes', 'daily_note_path',
        ]


class TaskDetailSerializer(serializers.ModelSerializer):
    """Serializer for full task detail."""
    project = serializers.SerializerMethodField()
    time_entries = TimeEntrySerializer(many=True, read_only=True)
    actual_hours = serializers.FloatField(source='get_actual_hours', read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'uuid', 'name', 'display_name', 'project',
            'status', 'priority', 'created', 'deadline',
            'estimated_hours', 'actual_hours', 'depends_on',
            'vault_path', 'description_markdown', 'time_entries',
        ]

    def get_project(self, obj):
        return {'id': obj.project.id, 'name': obj.project.name}


class GanttTaskSerializer(serializers.Serializer):
    """Serializer for Gantt chart task format (frappe-gantt compatible)."""
    id = serializers.CharField()
    name = serializers.CharField()
    start = serializers.DateField()
    end = serializers.DateField()
    progress = serializers.IntegerField()
    dependencies = serializers.CharField()
    custom_class = serializers.CharField()
    project_name = serializers.CharField()
```

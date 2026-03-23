import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import client from '@/api/client'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('@/components/layout/AppLayout.vue'),
    children: [
      {
        path: '',
        name: 'dashboard',
        component: () => import('@/views/Dashboard.vue'),
      },
      {
        path: 'pm',
        children: [
          {
            // /pm               → project list
            // /pm?project=<id>  → project task view (handled inside the component)
            path: '',
            name: 'pm-projects',
            component: () => import('@/views/pm/PmIndex.vue'),
          },
          {
            path: 'gantt',
            name: 'pm-gantt',
            component: () => import('@/views/pm/GanttView.vue'),
          },
        ],
      },
      {
        path: 'attendance',
        name: 'attendance',
        component: () => import('@/views/attendance/Upload.vue'),
      },
      {
        path: 'bom',
        name: 'bom',
        component: () => import('@/views/bom/Upload.vue'),
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Global navigation guard: verify the user has an active Django session.
// On any unrecognised 401/403 response, redirect to the Django admin login page.
//
// In development (Vite proxy), /admin is proxied to :8000, so the session
// cookie is set on the same origin as the Vue SPA (localhost:5173).
// In production, Nginx serves both the SPA and /admin from the same origin.
//
// next= points back to the SPA root (/) so Django redirects here after login.
let sessionVerified = false

router.beforeEach(async () => {
  if (sessionVerified) return true

  try {
    await client.get('/auth/me/')
    sessionVerified = true
    return true
  } catch {
    // Not authenticated — redirect to Django admin login (same-origin via proxy).
    window.location.href = `/admin/login/?next=${encodeURIComponent('/')}`
    return false
  }
})

export default router

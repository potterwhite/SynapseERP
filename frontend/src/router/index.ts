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
// On any unrecognised 401/403 response, redirect to the Django admin login page
// which sets the session cookie and then bounces back to the SPA.
let sessionVerified = false

router.beforeEach(async () => {
  if (sessionVerified) return true

  try {
    await client.get('/auth/me/')
    sessionVerified = true
    return true
  } catch {
    // Not authenticated — send to Django admin login.
    // next= points back to the SPA root so the user lands back after login.
    const loginUrl = `/admin/login/?next=${encodeURIComponent('/')}`
    window.location.href = loginUrl
    // Return false to abort the current navigation (we're doing a full redirect)
    return false
  }
})

export default router

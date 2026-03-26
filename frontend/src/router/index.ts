// Copyright (c) 2026 PotterWhite
// MIT License — see LICENSE in the project root.
//
// Vue Router configuration (Phase 5.7 — JWT auth guard).
//
// Guard flow:
//   1. Public routes (/login) always pass through.
//   2. For protected routes: check authStore.isAuthenticated.
//      If not yet verified, call fetchCurrentUser() once (restores session from localStorage).
//   3. If still unauthenticated: redirect to /login?redirect=<original path>.
//   4. Admin-only routes (meta.requiresAdmin): redirect non-admins to dashboard.

import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  // ── Public routes ──────────────────────────────────────────────────────────
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { public: true },
  },

  // ── Authenticated routes (AppLayout wrapper) ───────────────────────────────
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
          {
            path: 'sync',
            name: 'pm-sync',
            component: () => import('@/views/pm/SyncSettings.vue'),
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
      // ── Admin-only routes ──────────────────────────────────────────────────
      {
        path: 'admin/users',
        name: 'admin-users',
        component: () => import('@/views/admin/UsersView.vue'),
        meta: { requiresAdmin: true },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Global navigation guard — JWT-based (Phase 5.7)
// authChecked prevents repeated fetchCurrentUser() calls during the same session
let authChecked = false

router.beforeEach(async (to) => {
  // Public routes (e.g. /login) always pass through
  if (to.meta.public) return true

  const authStore = useAuthStore()

  // On the very first navigation, attempt to restore session from localStorage token
  if (!authChecked) {
    authChecked = true
    if (!authStore.isAuthenticated) {
      await authStore.fetchCurrentUser()
    }
  }

  // Not authenticated → redirect to Vue login page (preserves intended destination)
  if (!authStore.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  // Admin-only guard
  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    return { name: 'dashboard' }
  }

  return true
})

export default router

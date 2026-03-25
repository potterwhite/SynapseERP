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

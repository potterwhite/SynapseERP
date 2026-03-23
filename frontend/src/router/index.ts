import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

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
            path: '',
            name: 'pm-projects',
            component: () => import('@/views/pm/ProjectList.vue'),
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

export default router

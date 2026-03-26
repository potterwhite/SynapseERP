<!--
Copyright (c) 2026 PotterWhite

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
-->

<template>
  <div class="dashboard">

    <!-- ── Header ──────────────────────────────────────────────────── -->
    <n-flex justify="space-between" align="flex-end" style="margin-bottom: 24px;">
      <div>
        <n-h2 style="margin: 0; font-size: 24px; font-weight: 700;">
          Welcome back
        </n-h2>
        <n-text depth="3" style="font-size: 13px;">{{ todayLabel }}</n-text>
      </div>
    </n-flex>

    <!-- ── Notification ──────────────────────────────────────────── -->
    <n-alert
      v-if="notificationHtml"
      type="info"
      :bordered="false"
      style="margin-bottom: 24px;"
    >
      <div class="notification-body" v-html="notificationHtml" />
    </n-alert>

    <!-- ── PM Quick Stats ─────────────────────────────────────────── -->
    <n-grid :cols="4" :x-gap="16" :y-gap="16" responsive="screen" :item-responsive="true" style="margin-bottom: 28px;">
      <n-gi span="4 s:2 m:1">
        <n-card size="small" class="stat-card" hoverable @click="router.push('/pm')">
          <n-statistic :label="t('stat.total_projects')" :value="pmStats?.total_projects ?? 0">
            <template #prefix>
              <n-icon :component="FolderIcon" color="#2080f0" style="margin-right: 4px;" />
            </template>
          </n-statistic>
        </n-card>
      </n-gi>
      <n-gi span="4 s:2 m:1">
        <n-card size="small" class="stat-card" hoverable @click="router.push('/pm')">
          <n-statistic :label="t('stat.active_projects')" :value="pmStats?.active_projects ?? 0">
            <template #prefix>
              <n-icon :component="PlayIcon" color="#18a058" style="margin-right: 4px;" />
            </template>
          </n-statistic>
        </n-card>
      </n-gi>
      <n-gi span="4 s:2 m:1">
        <n-card size="small" class="stat-card" hoverable @click="router.push('/pm')">
          <n-statistic :label="t('stat.total_tasks')" :value="pmStats?.total_tasks ?? 0">
            <template #prefix>
              <n-icon :component="CheckboxIcon" color="#f0a020" style="margin-right: 4px;" />
            </template>
          </n-statistic>
        </n-card>
      </n-gi>
      <n-gi span="4 s:2 m:1">
        <n-card size="small" class="stat-card" hoverable @click="router.push('/pm')">
          <n-statistic :label="t('stat.hours_logged')" :value="pmStats?.total_hours_logged ?? 0">
            <template #prefix>
              <n-icon :component="TimeIcon" color="#8a2be2" style="margin-right: 4px;" />
            </template>
          </n-statistic>
        </n-card>
      </n-gi>
    </n-grid>

    <!-- ── Module Cards ───────────────────────────────────────────── -->
    <n-h3 style="margin: 0 0 16px; color: var(--n-text-color-2); font-size: 13px; text-transform: uppercase; letter-spacing: 0.08em;">
      {{ t('dashboard.modules') }}
    </n-h3>

    <n-spin v-if="loading" style="display: flex; justify-content: center; padding: 48px;" />

    <n-result
      v-else-if="error"
      status="error"
      :title="t('common.unknown_error')"
      :description="error"
    />

    <n-grid
      v-else
      :cols="3"
      :x-gap="16"
      :y-gap="16"
      responsive="screen"
      :item-responsive="true"
    >
      <n-gi v-for="mod in modules" :key="mod.key" span="3 m:1">
        <n-card
          hoverable
          style="cursor: pointer; transition: box-shadow 0.2s;"
          @click="router.push(mod.route)"
        >
          <n-flex align="center" gap="14">
            <n-icon
              :component="moduleIcon(mod.key)"
              :size="36"
              :color="moduleColor(mod.key)"
            />
            <div style="flex: 1; min-width: 0;">
              <div style="font-size: 16px; font-weight: 600; margin-bottom: 4px;">
                {{ mod.display_name }}
              </div>
              <n-text depth="3" style="font-size: 13px; display: block;">
                {{ mod.description }}
              </n-text>
            </div>
            <n-icon :component="ChevronIcon" depth="3" />
          </n-flex>
        </n-card>
      </n-gi>
    </n-grid>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  NAlert, NSpin, NResult, NH2, NH3, NGrid, NGi, NCard,
  NStatistic, NFlex, NIcon, NText,
} from 'naive-ui'
import type { Component } from 'vue'
import {
  FolderOutline as FolderIcon,
  PlayOutline as PlayIcon,
  CheckboxOutline as CheckboxIcon,
  TimeOutline as TimeIcon,
  BarChartOutline,
  ListOutline,
  LayersOutline,
  ChevronForwardOutline as ChevronIcon,
} from '@vicons/ionicons5'
import MarkdownIt from 'markdown-it'
import client from '@/api/client'
import type { PmStats } from '@/types/pm'

// ─── Types ───────────────────────────────────────────────────────────────────

interface Module {
  key: string
  display_name: string
  route: string
  description: string
}

interface DashboardResponse {
  notification: string | null
  modules: Module[]
}

// ─── State ───────────────────────────────────────────────────────────────────

const router = useRouter()
const md = new MarkdownIt()
const { t } = useI18n()

const loading = ref(true)
const error = ref<string | null>(null)
const notificationHtml = ref<string | null>(null)
const modules = ref<Module[]>([])
const pmStats = ref<PmStats | null>(null)

// ─── Computed ────────────────────────────────────────────────────────────────

const todayLabel = computed(() => {
  return new Date().toLocaleDateString(undefined, {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
  })
})

// ─── Module icon / color mapping ─────────────────────────────────────────────

const iconMap: Record<string, Component> = {
  pm: BarChartOutline,
  attendance: ListOutline,
  bom: LayersOutline,
}

const colorMap: Record<string, string> = {
  pm: '#2080f0',
  attendance: '#18a058',
  bom: '#f0a020',
}

function moduleIcon(key: string): Component {
  return iconMap[key] ?? FolderIcon
}

function moduleColor(key: string): string {
  return colorMap[key] ?? '#666'
}

// ─── Load ────────────────────────────────────────────────────────────────────

onMounted(async () => {
  try {
    const [dashRes, statsRes] = await Promise.allSettled([
      client.get<DashboardResponse>('/dashboard/'),
      client.get<PmStats>('/pm/stats/'),
    ])
    if (dashRes.status === 'fulfilled') {
      notificationHtml.value = dashRes.value.data.notification
        ? md.render(dashRes.value.data.notification)
        : null
      modules.value = dashRes.value.data.modules
    } else {
      throw dashRes.reason
    }
    if (statsRes.status === 'fulfilled') {
      pmStats.value = statsRes.value.data
    }
    // PM stats failure is non-critical — silently ignore
  } catch (e) {
    error.value = e instanceof Error ? e.message : t('common.unknown_error')
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.dashboard {
  max-width: 1100px;
}

.stat-card {
  cursor: pointer;
}

.notification-body :deep(h1),
.notification-body :deep(h2),
.notification-body :deep(h3) {
  margin: 0.5em 0 0.25em;
}
.notification-body :deep(p) {
  margin: 0.25em 0;
}
.notification-body :deep(ul),
.notification-body :deep(ol) {
  padding-left: 1.5em;
}
</style>

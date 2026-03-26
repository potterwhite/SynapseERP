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
  <div class="sync-settings">
    <n-page-header :title="t('sync.title')" :subtitle="t('sync.subtitle')">
      <template #extra>
        <n-space>
          <n-button
            type="primary"
            :loading="importing"
            :disabled="!syncConfig?.sync_enabled"
            @click="triggerImport"
          >
            <template #icon>
              <n-icon><CloudDownloadOutline /></n-icon>
            </template>
            {{ t('sync.import_btn') }}
          </n-button>
          <n-button
            :loading="exporting"
            :disabled="!syncConfig?.sync_enabled"
            @click="triggerExport"
          >
            <template #icon>
              <n-icon><CloudUploadOutline /></n-icon>
            </template>
            {{ t('sync.export_btn') }}
          </n-button>
        </n-space>
      </template>
    </n-page-header>

    <n-divider />

    <!-- Import filter card -->
    <n-card size="small" style="margin-bottom: 16px;">
      <template #header>
        <n-flex align="center" gap="8">
          <n-icon :component="FilterIcon" />
          <span>{{ t('sync.filter_card_title') }}</span>
        </n-flex>
      </template>
      <n-flex vertical gap="8">
        <n-input
          v-model:value="importNameFilter"
          clearable
          :placeholder="importFilterPlaceholder"
          @focus="importFilterFocused = true"
          @blur="importFilterFocused = false"
        >
          <template #suffix>
            <n-text depth="3" style="font-size: 12px; white-space: nowrap;">
              {{ t('sync.filter_suffix') }}
            </n-text>
          </template>
        </n-input>
        <!-- Persistent hint — always visible -->
        <n-text depth="3" style="font-size: 12px; line-height: 1.6;" v-html="t('sync.filter_hint')" />
      </n-flex>
    </n-card>

    <!-- Status cards -->
    <n-grid :cols="5" :x-gap="16" :y-gap="16" class="status-cards">
      <n-gi>
        <n-card size="small">
          <n-statistic :label="t('sync.status_card')">
            <template #prefix>
              <n-icon
                :component="syncConfig?.sync_enabled ? CheckmarkCircleOutline : CloseCircleOutline"
                :color="syncConfig?.sync_enabled ? '#18a058' : '#d03050'"
              />
            </template>
            {{ syncConfig?.sync_enabled ? t('sync.status_enabled') : t('sync.status_disabled') }}
          </n-statistic>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card size="small">
          <n-statistic :label="t('sync.db_projects')" :value="syncStatus?.db_projects ?? 0" />
        </n-card>
      </n-gi>
      <n-gi>
        <n-card size="small">
          <n-statistic :label="t('sync.db_tasks')" :value="syncStatus?.db_tasks ?? 0" />
        </n-card>
      </n-gi>
      <n-gi>
        <n-card size="small">
          <n-statistic
            :label="t('sync.vault_projects')"
            :value="syncStatus?.vault_projects ?? '—'"
          />
        </n-card>
      </n-gi>
      <n-gi>
        <n-card size="small">
          <n-statistic
            :label="t('sync.vault_tasks')"
            :value="syncStatus?.vault_tasks ?? '—'"
          />
        </n-card>
      </n-gi>
    </n-grid>

    <!-- Sync timestamps -->
    <n-grid :cols="2" :x-gap="16" :y-gap="16" style="margin-top: 16px;">
      <n-gi>
        <n-card size="small" :title="t('sync.last_import')">
          <n-text :depth="syncStatus?.last_import_at ? 1 : 3">
            {{ syncStatus?.last_import_at ? formatDatetime(syncStatus.last_import_at) : t('sync.never_synced') }}
          </n-text>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card size="small" :title="t('sync.last_export')">
          <n-text :depth="syncStatus?.last_export_at ? 1 : 3">
            {{ syncStatus?.last_export_at ? formatDatetime(syncStatus.last_export_at) : t('sync.never_exported') }}
          </n-text>
        </n-card>
      </n-gi>
    </n-grid>

    <n-divider />

    <!-- Auto-sync -->
    <n-card :title="t('sync.auto_sync_title')">
      <template #header-extra>
        <n-tag
          :type="watcherInfo?.watchdog_available ? 'success' : 'warning'"
          size="small"
        >
          {{ watcherInfo?.watchdog_available ? t('sync.watchdog_installed') : t('sync.watchdog_missing') }}
        </n-tag>
      </template>

      <n-alert
        v-if="!watcherInfo?.watchdog_available"
        type="warning"
        :show-icon="true"
        style="margin-bottom: 12px;"
      >
        <template #header>{{ t('sync.watchdog_missing') }}</template>
        Run <n-text code>pip install "watchdog>=4.0"</n-text> or
        <n-text code>./synapse prepare</n-text> to enable auto-sync.
      </n-alert>

      <n-descriptions :column="1" label-placement="left" label-style="width:160px" size="small">
        <n-descriptions-item :label="t('sync.watcher_how_label')">
          {{ t('sync.watcher_how_desc') }}
        </n-descriptions-item>
        <n-descriptions-item :label="t('sync.watcher_cmd_label')">
          <n-text code>{{ watcherInfo?.start_command ?? './synapse vault:watch' }}</n-text>
          <n-text depth="3" style="margin-left: 8px; font-size: 12px;">
            {{ t('sync.watcher_cmd_note') }}
          </n-text>
        </n-descriptions-item>
        <n-descriptions-item :label="t('sync.watcher_debounce_label')">
          <n-text code>./synapse vault:watch 3</n-text>
          <n-text depth="3" style="margin-left: 8px; font-size: 12px;">
            {{ t('sync.watcher_debounce_note') }}
          </n-text>
        </n-descriptions-item>
        <n-descriptions-item :label="t('sync.watcher_prod_label')">
          {{ t('sync.watcher_prod_desc') }}
        </n-descriptions-item>
      </n-descriptions>
    </n-card>

    <n-divider />

    <!-- Vault path configuration -->
    <n-card :title="t('sync.vault_path_title')">
      <template #header-extra>
        <n-tag :type="syncConfig?.sync_enabled ? 'success' : 'warning'" size="small">
          {{ syncConfig?.sync_enabled ? t('sync.vault_path_active') : t('sync.vault_path_not_configured') }}
        </n-tag>
      </template>

      <n-form label-placement="left" label-width="180px">
        <n-form-item :label="t('sync.vault_path_label')">
          <n-space vertical style="width: 100%;">
            <n-input
              v-model:value="editVaultPath"
              :placeholder="t('sync.vault_path_placeholder')"
              clearable
              @keydown.enter="saveVaultPath"
            />
            <n-space>
              <n-button type="primary" size="small" :loading="savingPath" @click="saveVaultPath">
                {{ t('sync.vault_path_save') }}
              </n-button>
              <n-button size="small" :disabled="!syncConfig?.vault_path" @click="clearVaultPath">
                {{ t('sync.vault_path_clear') }}
              </n-button>
            </n-space>
            <n-text depth="3" style="font-size: 12px;">
              {{ t('sync.vault_path_hint') }}
            </n-text>
          </n-space>
        </n-form-item>

        <n-form-item :label="t('sync.env_path_label')">
          <n-text :depth="syncConfig?.env_vault_path ? 1 : 3" style="font-family: monospace;">
            {{ syncConfig?.env_vault_path ?? t('common.none') }}
          </n-text>
        </n-form-item>

        <n-form-item :label="t('sync.effective_path_label')">
          <n-text
            :type="syncConfig?.sync_enabled ? 'success' : 'warning'"
            style="font-family: monospace; word-break: break-all;"
          >
            {{ syncConfig?.effective_vault_path ?? t('sync.effective_path_none') }}
          </n-text>
        </n-form-item>
      </n-form>
    </n-card>

    <!-- Last sync result -->
    <n-card v-if="lastResult" :title="t('sync.result_title')" style="margin-top: 16px;">
      <n-descriptions :column="3" label-placement="left" bordered size="small">
        <n-descriptions-item :label="t('sync.result_mode')">
          <n-tag :type="lastResult.mode === 'import' ? 'info' : 'warning'" size="small">
            {{ lastResult.mode }}
          </n-tag>
        </n-descriptions-item>
        <n-descriptions-item :label="t('sync.result_duration')">{{ lastResult.duration_ms }}ms</n-descriptions-item>
        <n-descriptions-item :label="t('sync.result_status')">
          <n-tag type="success" size="small">{{ lastResult.status }}</n-tag>
        </n-descriptions-item>
        <n-descriptions-item :label="t('sync.result_projects_created')">{{ lastResult.projects_created }}</n-descriptions-item>
        <n-descriptions-item :label="t('sync.result_projects_updated')">{{ lastResult.projects_updated }}</n-descriptions-item>
        <n-descriptions-item :label="t('sync.result_tasks_created')">{{ lastResult.tasks_created }}</n-descriptions-item>
        <n-descriptions-item :label="t('sync.result_tasks_updated')">{{ lastResult.tasks_updated }}</n-descriptions-item>
        <n-descriptions-item :label="t('sync.result_time_entries')">{{ lastResult.time_entries_created }}</n-descriptions-item>
        <n-descriptions-item :label="t('sync.result_skipped')">{{ lastResult.skipped }}</n-descriptions-item>
      </n-descriptions>
      <template v-if="lastResult.errors && lastResult.errors.length > 0">
        <n-divider />
        <n-alert type="warning" :title="t('sync.sync_errors')">
          <ul style="margin: 0; padding-left: 16px;">
            <li v-for="(err, i) in lastResult.errors" :key="i">{{ err }}</li>
          </ul>
        </n-alert>
      </template>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  NPageHeader, NButton, NIcon, NSpace, NDivider,
  NCard, NGrid, NGi, NStatistic, NText, NTag, NAlert,
  NForm, NFormItem, NInput, NDescriptions, NDescriptionsItem,
  NFlex,
  useMessage,
} from 'naive-ui'
import {
  CloudDownloadOutline,
  CloudUploadOutline,
  CheckmarkCircleOutline,
  CloseCircleOutline,
  FunnelOutline as FilterIcon,
} from '@vicons/ionicons5'
import client from '@/api/client'

// ─── Types ───────────────────────────────────────────────────────────────────

interface SyncStatus {
  enabled: boolean
  vault_path: string | null
  last_import_at: string | null
  last_export_at: string | null
  db_projects: number
  db_tasks: number
  vault_projects: number | null
  vault_tasks: number | null
}

interface SyncConfig {
  vault_path: string | null
  env_vault_path: string | null
  effective_vault_path: string | null
  sync_enabled: boolean
}

interface SyncResult {
  status: string
  mode: 'import' | 'export'
  dry_run: boolean
  duration_ms: number
  projects_created: number
  projects_updated: number
  tasks_created: number
  tasks_updated: number
  time_entries_created: number
  skipped: number
  errors: string[]
}

interface WatcherInfo {
  watchdog_available: boolean
  start_command: string
  notes: string
}

// ─── State ───────────────────────────────────────────────────────────────────

const message = useMessage()
const { t } = useI18n()

const syncStatus = ref<SyncStatus | null>(null)
const syncConfig = ref<SyncConfig | null>(null)
const watcherInfo = ref<WatcherInfo | null>(null)
const lastResult = ref<SyncResult | null>(null)

const importing = ref(false)
const exporting = ref(false)
const savingPath = ref(false)
const editVaultPath = ref('')
// Optional project name filter for import (comma-separated keywords)
const importNameFilter = ref('')
const importFilterFocused = ref(false)

const importFilterPlaceholder = computed(() =>
  importFilterFocused.value
    ? t('sync.filter_placeholder_focus')
    : t('sync.filter_placeholder_blur')
)

// ─── Load data ───────────────────────────────────────────────────────────────

async function loadStatus() {
  try {
    const [statusRes, configRes, watcherRes] = await Promise.all([
      client.get<SyncStatus>('/pm/sync/'),
      client.get<SyncConfig>('/pm/sync/config/'),
      client.get<WatcherInfo>('/pm/sync/watcher/'),
    ])
    syncStatus.value = statusRes.data
    syncConfig.value = configRes.data
    watcherInfo.value = watcherRes.data
    editVaultPath.value = configRes.data.vault_path ?? ''
  } catch (err: unknown) {
    message.error(t('sync.load_failed', { error: err instanceof Error ? err.message : t('common.unknown_error') }))
  }
}

onMounted(loadStatus)

// ─── Trigger import ──────────────────────────────────────────────────────────

async function triggerImport() {
  importing.value = true
  try {
    // Parse comma-separated name filter into a list; empty string means no filter.
    const nameFilter = importNameFilter.value
      .split(',')
      .map(s => s.trim())
      .filter(Boolean)

    const payload: Record<string, unknown> = { mode: 'import' }
    if (nameFilter.length > 0) payload.name_filter = nameFilter

    const res = await client.post<SyncResult>('/pm/sync/trigger/', payload)
    lastResult.value = res.data
    message.success(t('sync.import_success', { tasks_created: res.data.tasks_created, tasks_updated: res.data.tasks_updated }))
    await loadStatus()
  } catch (err: unknown) {
    message.error(t('sync.import_failed', { error: err instanceof Error ? err.message : t('common.unknown_error') }))
  } finally {
    importing.value = false
  }
}

// ─── Trigger export ──────────────────────────────────────────────────────────

async function triggerExport() {
  exporting.value = true
  try {
    const res = await client.post<SyncResult>('/pm/sync/trigger/', { mode: 'export' })
    lastResult.value = res.data
    message.success(t('sync.export_success', { tasks_created: res.data.tasks_created, tasks_updated: res.data.tasks_updated }))
    await loadStatus()
  } catch (err: unknown) {
    message.error(t('sync.export_failed', { error: err instanceof Error ? err.message : t('common.unknown_error') }))
  } finally {
    exporting.value = false
  }
}

// ─── Save vault path ─────────────────────────────────────────────────────────

async function saveVaultPath() {
  savingPath.value = true
  try {
    const res = await client.patch<SyncConfig>('/pm/sync/config/', {
      vault_path: editVaultPath.value.trim(),
    })
    syncConfig.value = res.data
    message.success(t('sync.path_saved'))
    await loadStatus()
  } catch (err: unknown) {
    message.error(t('sync.path_save_failed', { error: err instanceof Error ? err.message : t('common.unknown_error') }))
  } finally {
    savingPath.value = false
  }
}

async function clearVaultPath() {
  editVaultPath.value = ''
  await saveVaultPath()
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatDatetime(isoStr: string): string {
  try {
    return new Date(isoStr).toLocaleString()
  } catch {
    return isoStr
  }
}
</script>

<style scoped>
.sync-settings {
  padding: 0;
}

.status-cards {
  margin-top: 16px;
}
</style>

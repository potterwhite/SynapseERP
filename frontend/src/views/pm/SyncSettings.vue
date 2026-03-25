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
    <n-page-header title="Obsidian Sync" subtitle="Phase 5.3–5.5 — DB-Primary + Obsidian-Mirror">
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
            Import from Vault
          </n-button>
          <n-button
            :loading="exporting"
            :disabled="!syncConfig?.sync_enabled"
            @click="triggerExport"
          >
            <template #icon>
              <n-icon><CloudUploadOutline /></n-icon>
            </template>
            Export to Vault
          </n-button>
        </n-space>
      </template>
    </n-page-header>

    <n-divider />

    <!-- Status cards -->
    <n-grid :cols="3" :x-gap="16" :y-gap="16" class="status-cards">
      <!-- Sync enabled -->
      <n-gi>
        <n-card size="small">
          <n-statistic label="Sync Status">
            <template #prefix>
              <n-icon
                :component="syncConfig?.sync_enabled ? CheckmarkCircleOutline : CloseCircleOutline"
                :color="syncConfig?.sync_enabled ? '#18a058' : '#d03050'"
              />
            </template>
            {{ syncConfig?.sync_enabled ? 'Enabled' : 'Disabled' }}
          </n-statistic>
        </n-card>
      </n-gi>

      <!-- DB Projects -->
      <n-gi>
        <n-card size="small">
          <n-statistic label="Projects in DB" :value="syncStatus?.db_projects ?? 0" />
        </n-card>
      </n-gi>

      <!-- DB Tasks -->
      <n-gi>
        <n-card size="small">
          <n-statistic label="Tasks in DB" :value="syncStatus?.db_tasks ?? 0" />
        </n-card>
      </n-gi>
    </n-grid>

    <!-- Sync timestamps -->
    <n-grid :cols="2" :x-gap="16" :y-gap="16" style="margin-top: 16px;">
      <n-gi>
        <n-card size="small" title="Last Import (vault → DB)">
          <n-text :depth="syncStatus?.last_import_at ? 1 : 3">
            {{ syncStatus?.last_import_at
              ? formatDatetime(syncStatus.last_import_at)
              : 'Never synced' }}
          </n-text>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card size="small" title="Last Export (DB → vault)">
          <n-text :depth="syncStatus?.last_export_at ? 1 : 3">
            {{ syncStatus?.last_export_at
              ? formatDatetime(syncStatus.last_export_at)
              : 'Never exported' }}
          </n-text>
        </n-card>
      </n-gi>
    </n-grid>

    <n-divider />

    <!-- Auto-sync (Phase 5.5) -->
    <n-card title="Auto-Sync (Vault Watcher)">
      <template #header-extra>
        <n-tag
          :type="watcherInfo?.watchdog_available ? 'success' : 'warning'"
          size="small"
        >
          {{ watcherInfo?.watchdog_available ? 'watchdog installed' : 'watchdog not installed' }}
        </n-tag>
      </template>

      <n-alert
        v-if="!watcherInfo?.watchdog_available"
        type="warning"
        :show-icon="true"
        style="margin-bottom: 12px;"
      >
        <template #header>watchdog not installed</template>
        Run <n-text code>pip install "watchdog>=4.0"</n-text> or
        <n-text code>./synapse prepare</n-text> to enable auto-sync.
      </n-alert>

      <n-descriptions :column="1" label-placement="left" label-style="width:160px" size="small">
        <n-descriptions-item label="How it works">
          The vault watcher monitors your Obsidian vault for file changes
          and automatically runs an incremental import after a 5-second debounce window —
          no manual button click needed.
        </n-descriptions-item>
        <n-descriptions-item label="Start command">
          <n-text code>{{ watcherInfo?.start_command ?? './synapse vault:watch' }}</n-text>
          <n-text depth="3" style="margin-left: 8px; font-size: 12px;">
            (run in a separate terminal alongside the Django server)
          </n-text>
        </n-descriptions-item>
        <n-descriptions-item label="Custom debounce">
          <n-text code>./synapse vault:watch 3</n-text>
          <n-text depth="3" style="margin-left: 8px; font-size: 12px;">
            (3-second debounce, useful on fast machines)
          </n-text>
        </n-descriptions-item>
        <n-descriptions-item label="Production">
          Add a second Systemd unit pointing to
          <n-text code>manage.py vault_watch</n-text> alongside the Gunicorn unit.
        </n-descriptions-item>
      </n-descriptions>
    </n-card>

    <n-divider />

    <!-- Vault path configuration -->
    <n-card title="Vault Path Configuration">
      <template #header-extra>
        <n-tag
          :type="syncConfig?.sync_enabled ? 'success' : 'warning'"
          size="small"
        >
          {{ syncConfig?.sync_enabled ? 'Active' : 'Not configured' }}
        </n-tag>
      </template>

      <n-form label-placement="left" label-width="180px">
        <!-- Dynamic vault path (stored in DB, overrides .env) -->
        <n-form-item label="Dynamic Vault Path">
          <n-space vertical style="width: 100%;">
            <n-input
              v-model:value="editVaultPath"
              placeholder="/absolute/path/to/your/obsidian/vault"
              clearable
              @keydown.enter="saveVaultPath"
            />
            <n-space>
              <n-button
                type="primary"
                size="small"
                :loading="savingPath"
                @click="saveVaultPath"
              >
                Save
              </n-button>
              <n-button
                size="small"
                :disabled="!syncConfig?.vault_path"
                @click="clearVaultPath"
              >
                Clear (use .env)
              </n-button>
            </n-space>
            <n-text depth="3" style="font-size: 12px;">
              Set here to override the .env value. Leave empty to use OBSIDIAN_VAULT_PATH from .env.
            </n-text>
          </n-space>
        </n-form-item>

        <!-- .env value (read-only) -->
        <n-form-item label=".env OBSIDIAN_VAULT_PATH">
          <n-text :depth="syncConfig?.env_vault_path ? 1 : 3" style="font-family: monospace;">
            {{ syncConfig?.env_vault_path ?? '(not set)' }}
          </n-text>
        </n-form-item>

        <!-- Effective path (resolved) -->
        <n-form-item label="Effective Vault Path">
          <n-text
            :type="syncConfig?.sync_enabled ? 'success' : 'warning'"
            style="font-family: monospace; word-break: break-all;"
          >
            {{ syncConfig?.effective_vault_path ?? '(none — sync disabled)' }}
          </n-text>
        </n-form-item>
      </n-form>
    </n-card>

    <!-- Last sync result -->
    <n-card v-if="lastResult" title="Last Sync Result" style="margin-top: 16px;">
      <n-descriptions :column="3" label-placement="left" bordered size="small">
        <n-descriptions-item label="Mode">
          <n-tag :type="lastResult.mode === 'import' ? 'info' : 'warning'" size="small">
            {{ lastResult.mode }}
          </n-tag>
        </n-descriptions-item>
        <n-descriptions-item label="Duration">
          {{ lastResult.duration_ms }}ms
        </n-descriptions-item>
        <n-descriptions-item label="Status">
          <n-tag type="success" size="small">{{ lastResult.status }}</n-tag>
        </n-descriptions-item>
        <n-descriptions-item label="Projects Created">{{ lastResult.projects_created }}</n-descriptions-item>
        <n-descriptions-item label="Projects Updated">{{ lastResult.projects_updated }}</n-descriptions-item>
        <n-descriptions-item label="Tasks Created">{{ lastResult.tasks_created }}</n-descriptions-item>
        <n-descriptions-item label="Tasks Updated">{{ lastResult.tasks_updated }}</n-descriptions-item>
        <n-descriptions-item label="Time Entries Created">{{ lastResult.time_entries_created }}</n-descriptions-item>
        <n-descriptions-item label="Skipped">{{ lastResult.skipped }}</n-descriptions-item>
      </n-descriptions>
      <template v-if="lastResult.errors && lastResult.errors.length > 0">
        <n-divider />
        <n-alert type="warning" title="Sync Errors">
          <ul style="margin: 0; padding-left: 16px;">
            <li v-for="(err, i) in lastResult.errors" :key="i">{{ err }}</li>
          </ul>
        </n-alert>
      </template>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  NPageHeader, NButton, NIcon, NSpace, NDivider,
  NCard, NGrid, NGi, NStatistic, NText, NTag, NAlert,
  NForm, NFormItem, NInput, NDescriptions, NDescriptionsItem,
  useMessage,
} from 'naive-ui'
import {
  CloudDownloadOutline,
  CloudUploadOutline,
  CheckmarkCircleOutline,
  CloseCircleOutline,
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

const syncStatus = ref<SyncStatus | null>(null)
const syncConfig = ref<SyncConfig | null>(null)
const watcherInfo = ref<WatcherInfo | null>(null)
const lastResult = ref<SyncResult | null>(null)

const importing = ref(false)
const exporting = ref(false)
const savingPath = ref(false)
const editVaultPath = ref('')

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
    message.error('Failed to load sync status: ' + (err instanceof Error ? err.message : 'Unknown error'))
  }
}

onMounted(loadStatus)

// ─── Trigger import ──────────────────────────────────────────────────────────

async function triggerImport() {
  importing.value = true
  try {
    const res = await client.post<SyncResult>('/pm/sync/trigger/', { mode: 'import' })
    lastResult.value = res.data
    message.success(`Import complete: ${res.data.tasks_created} tasks created, ${res.data.tasks_updated} updated`)
    await loadStatus()
  } catch (err: unknown) {
    message.error('Import failed: ' + (err instanceof Error ? err.message : 'Unknown error'))
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
    message.success(`Export complete: ${res.data.tasks_created} files created, ${res.data.tasks_updated} updated`)
    await loadStatus()
  } catch (err: unknown) {
    message.error('Export failed: ' + (err instanceof Error ? err.message : 'Unknown error'))
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
    message.success('Vault path saved')
    await loadStatus()
  } catch (err: unknown) {
    message.error('Failed to save vault path: ' + (err instanceof Error ? err.message : 'Unknown error'))
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
            Import from Vault
          </n-button>
          <n-button
            :loading="exporting"
            :disabled="!syncConfig?.sync_enabled"
            @click="triggerExport"
          >
            <template #icon>
              <n-icon><CloudUploadOutline /></n-icon>
            </template>
            Export to Vault
          </n-button>
        </n-space>
      </template>
    </n-page-header>

    <n-divider />

    <!-- Status cards -->
    <n-grid :cols="3" :x-gap="16" :y-gap="16" class="status-cards">
      <!-- Sync enabled -->
      <n-gi>
        <n-card size="small">
          <n-statistic label="Sync Status">
            <template #prefix>
              <n-icon
                :component="syncConfig?.sync_enabled ? CheckmarkCircleOutline : CloseCircleOutline"
                :color="syncConfig?.sync_enabled ? '#18a058' : '#d03050'"
              />
            </template>
            {{ syncConfig?.sync_enabled ? 'Enabled' : 'Disabled' }}
          </n-statistic>
        </n-card>
      </n-gi>

      <!-- DB Projects -->
      <n-gi>
        <n-card size="small">
          <n-statistic label="Projects in DB" :value="syncStatus?.db_projects ?? 0" />
        </n-card>
      </n-gi>

      <!-- DB Tasks -->
      <n-gi>
        <n-card size="small">
          <n-statistic label="Tasks in DB" :value="syncStatus?.db_tasks ?? 0" />
        </n-card>
      </n-gi>
    </n-grid>

    <!-- Sync timestamps -->
    <n-grid :cols="2" :x-gap="16" :y-gap="16" style="margin-top: 16px;">
      <n-gi>
        <n-card size="small" title="Last Import (vault → DB)">
          <n-text :depth="syncStatus?.last_import_at ? 1 : 3">
            {{ syncStatus?.last_import_at
              ? formatDatetime(syncStatus.last_import_at)
              : 'Never synced' }}
          </n-text>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card size="small" title="Last Export (DB → vault)">
          <n-text :depth="syncStatus?.last_export_at ? 1 : 3">
            {{ syncStatus?.last_export_at
              ? formatDatetime(syncStatus.last_export_at)
              : 'Never exported' }}
          </n-text>
        </n-card>
      </n-gi>
    </n-grid>

    <n-divider />

    <!-- Vault path configuration -->
    <n-card title="Vault Path Configuration">
      <template #header-extra>
        <n-tag
          :type="syncConfig?.sync_enabled ? 'success' : 'warning'"
          size="small"
        >
          {{ syncConfig?.sync_enabled ? 'Active' : 'Not configured' }}
        </n-tag>
      </template>

      <n-form label-placement="left" label-width="180px">
        <!-- Dynamic vault path (stored in DB, overrides .env) -->
        <n-form-item label="Dynamic Vault Path">
          <n-space vertical style="width: 100%;">
            <n-input
              v-model:value="editVaultPath"
              placeholder="/absolute/path/to/your/obsidian/vault"
              clearable
              @keydown.enter="saveVaultPath"
            />
            <n-space>
              <n-button
                type="primary"
                size="small"
                :loading="savingPath"
                @click="saveVaultPath"
              >
                Save
              </n-button>
              <n-button
                size="small"
                :disabled="!syncConfig?.vault_path"
                @click="clearVaultPath"
              >
                Clear (use .env)
              </n-button>
            </n-space>
            <n-text depth="3" style="font-size: 12px;">
              Set here to override the .env value. Leave empty to use OBSIDIAN_VAULT_PATH from .env.
            </n-text>
          </n-space>
        </n-form-item>

        <!-- .env value (read-only) -->
        <n-form-item label=".env OBSIDIAN_VAULT_PATH">
          <n-text :depth="syncConfig?.env_vault_path ? 1 : 3" style="font-family: monospace;">
            {{ syncConfig?.env_vault_path ?? '(not set)' }}
          </n-text>
        </n-form-item>

        <!-- Effective path (resolved) -->
        <n-form-item label="Effective Vault Path">
          <n-text
            :type="syncConfig?.sync_enabled ? 'success' : 'warning'"
            style="font-family: monospace; word-break: break-all;"
          >
            {{ syncConfig?.effective_vault_path ?? '(none — sync disabled)' }}
          </n-text>
        </n-form-item>
      </n-form>
    </n-card>

    <!-- Last sync result -->
    <n-card v-if="lastResult" title="Last Sync Result" style="margin-top: 16px;">
      <n-descriptions :column="3" label-placement="left" bordered size="small">
        <n-descriptions-item label="Mode">
          <n-tag :type="lastResult.mode === 'import' ? 'info' : 'warning'" size="small">
            {{ lastResult.mode }}
          </n-tag>
        </n-descriptions-item>
        <n-descriptions-item label="Duration">
          {{ lastResult.duration_ms }}ms
        </n-descriptions-item>
        <n-descriptions-item label="Status">
          <n-tag type="success" size="small">{{ lastResult.status }}</n-tag>
        </n-descriptions-item>
        <n-descriptions-item label="Projects Created">{{ lastResult.projects_created }}</n-descriptions-item>
        <n-descriptions-item label="Projects Updated">{{ lastResult.projects_updated }}</n-descriptions-item>
        <n-descriptions-item label="Tasks Created">{{ lastResult.tasks_created }}</n-descriptions-item>
        <n-descriptions-item label="Tasks Updated">{{ lastResult.tasks_updated }}</n-descriptions-item>
        <n-descriptions-item label="Time Entries Created">{{ lastResult.time_entries_created }}</n-descriptions-item>
        <n-descriptions-item label="Skipped">{{ lastResult.skipped }}</n-descriptions-item>
      </n-descriptions>
      <template v-if="lastResult.errors && lastResult.errors.length > 0">
        <n-divider />
        <n-alert type="warning" title="Sync Errors">
          <ul style="margin: 0; padding-left: 16px;">
            <li v-for="(err, i) in lastResult.errors" :key="i">{{ err }}</li>
          </ul>
        </n-alert>
      </template>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  NPageHeader, NButton, NIcon, NSpace, NDivider,
  NCard, NGrid, NGi, NStatistic, NText, NTag,
  NForm, NFormItem, NInput, NAlert, NDescriptions, NDescriptionsItem,
  useMessage,
} from 'naive-ui'
import {
  CloudDownloadOutline,
  CloudUploadOutline,
  CheckmarkCircleOutline,
  CloseCircleOutline,
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

// ─── State ───────────────────────────────────────────────────────────────────

const message = useMessage()

const syncStatus = ref<SyncStatus | null>(null)
const syncConfig = ref<SyncConfig | null>(null)
const lastResult = ref<SyncResult | null>(null)

const importing = ref(false)
const exporting = ref(false)
const savingPath = ref(false)
const editVaultPath = ref('')

// ─── Load data ───────────────────────────────────────────────────────────────

async function loadStatus() {
  try {
    const [statusRes, configRes] = await Promise.all([
      client.get<SyncStatus>('/pm/sync/'),
      client.get<SyncConfig>('/pm/sync/config/'),
    ])
    syncStatus.value = statusRes.data
    syncConfig.value = configRes.data
    editVaultPath.value = configRes.data.vault_path ?? ''
  } catch (err: unknown) {
    message.error('Failed to load sync status: ' + (err instanceof Error ? err.message : 'Unknown error'))
  }
}

onMounted(loadStatus)

// ─── Trigger import ──────────────────────────────────────────────────────────

async function triggerImport() {
  importing.value = true
  try {
    const res = await client.post<SyncResult>('/pm/sync/trigger/', { mode: 'import' })
    lastResult.value = res.data
    message.success(`Import complete: ${res.data.tasks_created} tasks created, ${res.data.tasks_updated} updated`)
    await loadStatus()
  } catch (err: unknown) {
    message.error('Import failed: ' + (err instanceof Error ? err.message : 'Unknown error'))
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
    message.success(`Export complete: ${res.data.tasks_created} files created, ${res.data.tasks_updated} updated`)
    await loadStatus()
  } catch (err: unknown) {
    message.error('Export failed: ' + (err instanceof Error ? err.message : 'Unknown error'))
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
    message.success('Vault path saved')
    await loadStatus()
  } catch (err: unknown) {
    message.error('Failed to save vault path: ' + (err instanceof Error ? err.message : 'Unknown error'))
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

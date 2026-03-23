<template>
  <div>
    <!-- Notification panel (shown only when a notification exists) -->
    <n-alert
      v-if="notificationHtml"
      type="info"
      :bordered="false"
      style="margin-bottom: 24px;"
    >
      <!-- v-html: safe here because content comes from trusted Django admin input -->
      <div class="notification-body" v-html="notificationHtml" />
    </n-alert>

    <!-- Loading state -->
    <n-spin v-if="loading" style="display: flex; justify-content: center; padding: 48px;" />

    <!-- Error state -->
    <n-result
      v-else-if="error"
      status="error"
      title="Failed to load dashboard"
      :description="error"
    />

    <!-- Module cards -->
    <template v-else>
      <n-h2>工具箱 / Toolbox</n-h2>
      <n-grid :cols="3" :x-gap="16" :y-gap="16" responsive="screen" :item-responsive="true">
        <n-gi v-for="mod in modules" :key="mod.key" span="3 m:1">
          <n-card
            hoverable
            :title="mod.display_name"
            style="cursor: pointer;"
            @click="router.push(mod.route)"
          >
            {{ mod.description }}
          </n-card>
        </n-gi>
      </n-grid>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { NAlert, NSpin, NResult, NH2, NGrid, NGi, NCard } from 'naive-ui'
// markdown-it: converts Markdown text to an HTML string in the browser
import MarkdownIt from 'markdown-it'
import client from '@/api/client'

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

const router = useRouter()
const md = new MarkdownIt()

const loading = ref(true)
const error = ref<string | null>(null)
const notificationHtml = ref<string | null>(null)
const modules = ref<Module[]>([])

onMounted(async () => {
  try {
    const { data } = await client.get<DashboardResponse>('/dashboard/')
    notificationHtml.value = data.notification ? md.render(data.notification) : null
    modules.value = data.modules
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Unknown error'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
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

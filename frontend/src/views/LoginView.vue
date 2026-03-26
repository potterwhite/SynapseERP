<!--
Copyright (c) 2026 PotterWhite
MIT License — see LICENSE in the project root.

Custom JWT login page (Phase 5.7).
Replaces the Django admin login redirect that was used in Phase ≤5.6.
-->

<template>
  <n-config-provider :theme="naiveTheme">
    <n-message-provider>
      <div class="login-wrapper">
        <div class="login-card">
          <!-- Logo / Title -->
          <div class="login-header">
            <n-h2 style="margin: 0;">SynapseERP</n-h2>
            <n-text depth="3" style="font-size: 13px;">{{ appStore.appVersion }}</n-text>
          </div>

          <!-- Error alert -->
          <n-alert
            v-if="errorMsg"
            type="error"
            :title="errorMsg"
            closable
            style="margin-bottom: 20px;"
            @close="errorMsg = ''"
          />

          <!-- Login form -->
          <n-form ref="formRef" :model="formData" :rules="rules" @submit.prevent="handleLogin">
            <n-form-item path="username" :label="t('login.username_label')">
              <n-input
                v-model:value="formData.username"
                :placeholder="t('login.username_placeholder')"
                :disabled="loading"
                @keydown.enter="handleLogin"
              />
            </n-form-item>

            <n-form-item path="password" :label="t('login.password_label')">
              <n-input
                v-model:value="formData.password"
                type="password"
                show-password-on="click"
                :placeholder="t('login.password_placeholder')"
                :disabled="loading"
                @keydown.enter="handleLogin"
              />
            </n-form-item>

            <n-button
              type="primary"
              block
              :loading="loading"
              style="margin-top: 8px;"
              @click="handleLogin"
            >
              {{ t('login.btn') }}
            </n-button>
          </n-form>

          <!-- Theme toggle -->
          <div style="text-align: center; margin-top: 20px;">
            <n-button quaternary size="small" @click="appStore.toggleTheme">
              <template #icon>
                <n-icon><component :is="appStore.theme === 'dark' ? SunnyOutline : MoonOutline" /></n-icon>
              </template>
              {{ appStore.theme === 'dark' ? t('login.light_mode') : t('login.dark_mode') }}
            </n-button>
          </div>

          <!-- Registration link -->
          <div style="text-align: center; margin-top: 12px;">
            <n-button text @click="router.push('/register')">
              {{ t('login.no_account') }}
            </n-button>
          </div>
        </div>
      </div>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  NConfigProvider,
  NMessageProvider,
  NForm,
  NFormItem,
  NInput,
  NButton,
  NAlert,
  NH2,
  NText,
  NIcon,
  darkTheme,
} from 'naive-ui'
import type { FormInst, FormRules } from 'naive-ui'
import { MoonOutline, SunnyOutline } from '@vicons/ionicons5'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'

const router = useRouter()
const authStore = useAuthStore()
const appStore = useAppStore()
const { t } = useI18n()

const naiveTheme = computed(() => appStore.theme === 'dark' ? darkTheme : null)

const formRef = ref<FormInst | null>(null)
const loading = ref(false)
const errorMsg = ref('')

const formData = ref({
  username: '',
  password: '',
})

const rules: FormRules = {
  username: [{ required: true, message: t('login.username_required'), trigger: 'blur' }],
  password: [{ required: true, message: t('login.password_required'), trigger: 'blur' }],
}

async function handleLogin() {
  if (loading.value) return

  try {
    await formRef.value?.validate()
  } catch {
    return // validation failed — n-form shows inline errors
  }

  loading.value = true
  errorMsg.value = ''

  try {
    await authStore.login(formData.value.username, formData.value.password)
    // Redirect to the page the user was trying to access (or dashboard)
    const redirect = (router.currentRoute.value.query.redirect as string) || '/'
    router.push(redirect)
  } catch (err: unknown) {
    errorMsg.value = err instanceof Error ? err.message : t('auth.login_failed')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrapper {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--n-color, #f5f5f5);
  padding: 24px;
}

.login-card {
  width: 100%;
  max-width: 400px;
  background: var(--n-card-color, #fff);
  border-radius: 12px;
  padding: 40px 36px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}
</style>

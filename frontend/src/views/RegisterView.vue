<!--
Copyright (c) 2026 PotterWhite
MIT License — see LICENSE in the project root.

Self-registration page (Phase 5.9).
New users are created with role='viewer'.
Admins can promote them via the User Management page (/admin/users).
-->

<template>
  <n-config-provider :theme="naiveTheme">
    <n-message-provider>
      <div class="login-wrapper">
        <div class="login-card">
          <!-- Logo / Title -->
          <div class="login-header">
            <n-h2 style="margin: 0;">SynapseERP</n-h2>
            <n-text depth="3" style="font-size: 13px;">Create an account</n-text>
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

          <!-- Registration form -->
          <n-form ref="formRef" :model="formData" :rules="rules" @submit.prevent="handleRegister">
            <n-form-item path="username" label="Username">
              <n-input
                v-model:value="formData.username"
                placeholder="Choose a username"
                :disabled="loading"
              />
            </n-form-item>

            <n-form-item path="email" label="Email (optional)">
              <n-input
                v-model:value="formData.email"
                placeholder="your@email.com"
                :disabled="loading"
              />
            </n-form-item>

            <n-form-item path="password" label="Password">
              <n-input
                v-model:value="formData.password"
                type="password"
                show-password-on="click"
                placeholder="At least 8 characters"
                :disabled="loading"
              />
            </n-form-item>

            <n-form-item path="password_confirm" label="Confirm password">
              <n-input
                v-model:value="formData.password_confirm"
                type="password"
                show-password-on="click"
                placeholder="Repeat password"
                :disabled="loading"
                @keydown.enter="handleRegister"
              />
            </n-form-item>

            <n-button
              type="primary"
              block
              :loading="loading"
              style="margin-top: 8px;"
              @click="handleRegister"
            >
              Create account
            </n-button>
          </n-form>

          <!-- Role info note -->
          <n-alert type="info" style="margin-top: 16px;" :show-icon="false">
            <n-text depth="3" style="font-size: 12px;">
              New accounts start with <strong>Viewer</strong> access.
              Contact an admin to get Editor or Admin permissions.
            </n-text>
          </n-alert>

          <!-- Back to login -->
          <div style="text-align: center; margin-top: 16px;">
            <n-button text @click="router.push('/login')">
              Already have an account? Sign in
            </n-button>
          </div>

          <!-- Theme toggle -->
          <div style="text-align: center; margin-top: 12px;">
            <n-button quaternary size="small" @click="appStore.toggleTheme">
              <template #icon>
                <n-icon><component :is="appStore.theme === 'dark' ? SunnyOutline : MoonOutline" /></n-icon>
              </template>
              {{ appStore.theme === 'dark' ? 'Light mode' : 'Dark mode' }}
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
import { authApi } from '@/api/auth'
import { ACCESS_TOKEN_KEY, REFRESH_TOKEN_KEY } from '@/api/client'

const router = useRouter()
const authStore = useAuthStore()
const appStore = useAppStore()

const naiveTheme = computed(() => appStore.theme === 'dark' ? darkTheme : null)

const formRef = ref<FormInst | null>(null)
const loading = ref(false)
const errorMsg = ref('')

const formData = ref({
  username: '',
  email: '',
  password: '',
  password_confirm: '',
})

const rules: FormRules = {
  username: [{ required: true, message: 'Username is required', trigger: 'blur' }],
  password: [
    { required: true, message: 'Password is required', trigger: 'blur' },
    { min: 8, message: 'Password must be at least 8 characters', trigger: 'blur' },
  ],
  password_confirm: [
    { required: true, message: 'Please confirm your password', trigger: 'blur' },
    {
      validator: (_rule: unknown, value: string) => {
        if (value !== formData.value.password) {
          return new Error('Passwords do not match')
        }
        return true
      },
      trigger: ['blur', 'input'],
    },
  ],
}

async function handleRegister() {
  if (loading.value) return

  try {
    await formRef.value?.validate()
  } catch {
    return // validation failed — n-form shows inline errors
  }

  loading.value = true
  errorMsg.value = ''

  try {
    const payload = {
      username: formData.value.username,
      email: formData.value.email || undefined,
      password: formData.value.password,
      password_confirm: formData.value.password_confirm,
    }
    const res = await authApi.register(payload)

    // Store tokens and hydrate auth store (same flow as login)
    localStorage.setItem(ACCESS_TOKEN_KEY, res.data.access)
    localStorage.setItem(REFRESH_TOKEN_KEY, res.data.refresh)
    authStore.user = res.data.user

    // Redirect to dashboard
    router.push('/')
  } catch (err: unknown) {
    // Extract first error message from DRF validation response
    if (err && typeof err === 'object' && 'response' in err) {
      const resp = (err as { response?: { data?: Record<string, unknown> } }).response
      if (resp?.data) {
        const firstField = Object.values(resp.data)[0]
        if (Array.isArray(firstField) && firstField.length > 0) {
          errorMsg.value = String(firstField[0])
          return
        }
      }
    }
    errorMsg.value = err instanceof Error ? err.message : 'Registration failed. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* Reuses the same layout as LoginView for visual consistency */
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

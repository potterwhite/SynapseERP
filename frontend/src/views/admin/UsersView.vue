<!--
Copyright (c) 2026 PotterWhite
MIT License — see LICENSE in the project root.

User Management view — admin only (Phase 5.7).
Allows creating, editing (role + allowed_tags), and deleting users.
-->

<template>
  <div>
    <!-- Page header -->
    <n-flex justify="space-between" align="center" style="margin-bottom: 20px;">
      <n-h2 style="margin: 0;">User Management</n-h2>
      <n-button type="primary" @click="openCreateModal">
        <template #icon><n-icon><PersonAddOutline /></n-icon></template>
        New User
      </n-button>
    </n-flex>

    <!-- Users table -->
    <n-data-table
      :columns="columns"
      :data="users"
      :loading="loading"
      :pagination="{ pageSize: 20 }"
      :bordered="false"
      striped
    />

    <!-- Create / Edit modal -->
    <n-modal
      v-model:show="modalVisible"
      preset="card"
      :title="editingUser ? 'Edit User' : 'New User'"
      style="max-width: 480px;"
      :segmented="true"
    >
      <n-form ref="formRef" :model="formData" :rules="formRules" label-placement="left" label-width="110px">
        <template v-if="!editingUser">
          <n-form-item label="Username" path="username">
            <n-input v-model:value="formData.username" placeholder="e.g. alice" />
          </n-form-item>
          <n-form-item label="Email" path="email">
            <n-input v-model:value="formData.email" placeholder="alice@example.com (optional)" />
          </n-form-item>
          <n-form-item label="Password" path="password">
            <n-input v-model:value="formData.password" type="password" show-password-on="click" placeholder="Min. 8 characters" />
          </n-form-item>
        </template>

        <n-form-item label="Role" path="role">
          <n-select
            v-model:value="formData.role"
            :options="roleOptions"
            placeholder="Select role"
          />
        </n-form-item>

        <n-form-item label="Allowed Tags" path="allowed_tags">
          <n-dynamic-tags v-model:value="formData.allowed_tags" />
        </n-form-item>
        <n-text depth="3" style="font-size: 12px; margin-left: 110px; margin-top: -8px; display: block;">
          Leave empty to deny access to all tagged projects. Untagged projects are always visible.
        </n-text>
      </n-form>

      <template #action>
        <n-space justify="end">
          <n-button @click="modalVisible = false">Cancel</n-button>
          <n-button type="primary" :loading="saving" @click="handleSave">
            {{ editingUser ? 'Save Changes' : 'Create User' }}
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import {
  NDataTable, NButton, NModal, NForm, NFormItem, NInput, NSelect,
  NSpace, NFlex, NH2, NIcon, NText, NDynamicTags,
  useMessage,
} from 'naive-ui'
import type { DataTableColumns, FormInst, FormRules } from 'naive-ui'
import { PersonAddOutline, CreateOutline, TrashOutline } from '@vicons/ionicons5'
import { userApi } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import type { User, UserRole } from '@/types/auth'

const message = useMessage()
const authStore = useAuthStore()

// ── State ──────────────────────────────────────────────────────────────────
const users = ref<User[]>([])
const loading = ref(false)
const saving = ref(false)
const modalVisible = ref(false)
const editingUser = ref<User | null>(null)
const formRef = ref<FormInst | null>(null)

const formData = ref({
  username: '',
  email: '',
  password: '',
  role: 'viewer' as UserRole,
  allowed_tags: [] as string[],
})

// ── Config ─────────────────────────────────────────────────────────────────
const roleOptions = [
  { label: 'Admin — full access', value: 'admin' },
  { label: 'Editor — read/write (tag-filtered)', value: 'editor' },
  { label: 'Viewer — read-only (tag-filtered)', value: 'viewer' },
]

const formRules: FormRules = {
  username: [{ required: true, message: 'Username is required', trigger: 'blur' }],
  password: [{ required: true, min: 8, message: 'Password must be at least 8 characters', trigger: 'blur' }],
  role: [{ required: true, message: 'Role is required', trigger: 'change' }],
}

// ── Table columns ──────────────────────────────────────────────────────────
const columns: DataTableColumns<User> = [
  { title: 'ID', key: 'id', width: 60 },
  { title: 'Username', key: 'username' },
  { title: 'Email', key: 'email', render: (row) => row.email || '—' },
  {
    title: 'Role',
    key: 'role',
    render: (row) => {
      const colorMap: Record<string, string> = {
        admin: '#d03050',
        editor: '#d4930a',
        viewer: '#18a058',
      }
      return h('span', {
        style: { color: colorMap[row.role] || 'inherit', fontWeight: '600', fontSize: '13px' },
      }, row.role)
    },
  },
  {
    title: 'Allowed Tags',
    key: 'allowed_tags',
    render: (row) => (row.allowed_tags?.length ? row.allowed_tags.join(', ') : '— (all untagged)'),
  },
  {
    title: 'Actions',
    key: 'actions',
    width: 100,
    render: (row) =>
      h(NSpace, { size: 'small' }, {
        default: () => [
          h(NButton, {
            quaternary: true,
            circle: true,
            size: 'small',
            onClick: () => openEditModal(row),
          }, { icon: () => h(NIcon, null, { default: () => h(CreateOutline) }) }),
          h(NButton, {
            quaternary: true,
            circle: true,
            size: 'small',
            disabled: row.id === authStore.user?.id, // cannot delete yourself
            onClick: () => handleDelete(row),
          }, { icon: () => h(NIcon, { style: 'color: #d03050' }, { default: () => h(TrashOutline) }) }),
        ],
      }),
  },
]

// ── Data loading ───────────────────────────────────────────────────────────
async function loadUsers() {
  loading.value = true
  try {
    const res = await userApi.list()
    users.value = res.data
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : 'Failed to load users')
  } finally {
    loading.value = false
  }
}

// ── Modal helpers ──────────────────────────────────────────────────────────
function resetForm() {
  formData.value = { username: '', email: '', password: '', role: 'viewer', allowed_tags: [] }
}

function openCreateModal() {
  editingUser.value = null
  resetForm()
  modalVisible.value = true
}

function openEditModal(user: User) {
  editingUser.value = user
  formData.value = {
    username: user.username,
    email: user.email,
    password: '',         // not shown in edit mode
    role: user.role,
    allowed_tags: [...(user.allowed_tags || [])],
  }
  modalVisible.value = true
}

// ── Save ───────────────────────────────────────────────────────────────────
async function handleSave() {
  try {
    if (!editingUser.value) {
      // Create: validate all fields including password
      await formRef.value?.validate()
    } else {
      // Edit: validate only role (password field is hidden)
      await formRef.value?.validate(undefined, (rule) => !rule.key?.includes('password') && !rule.key?.includes('username'))
    }
  } catch {
    return
  }

  saving.value = true
  try {
    if (editingUser.value) {
      await userApi.update(editingUser.value.id, {
        role: formData.value.role,
        allowed_tags: formData.value.allowed_tags,
        email: formData.value.email,
      })
      message.success('User updated')
    } else {
      await userApi.create({
        username: formData.value.username,
        email: formData.value.email,
        password: formData.value.password,
        role: formData.value.role,
        allowed_tags: formData.value.allowed_tags,
      })
      message.success('User created')
    }
    modalVisible.value = false
    await loadUsers()
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : 'Save failed')
  } finally {
    saving.value = false
  }
}

// ── Delete ─────────────────────────────────────────────────────────────────
async function handleDelete(user: User) {
  if (!confirm(`Delete user "${user.username}"? This cannot be undone.`)) return
  try {
    await userApi.delete(user.id)
    message.success(`User "${user.username}" deleted`)
    await loadUsers()
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : 'Delete failed')
  }
}

onMounted(() => loadUsers())
</script>

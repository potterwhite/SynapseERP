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
  <n-modal
    v-model:show="visible"
    preset="card"
    :title="isEdit ? 'Edit Project' : 'New Project'"
    style="width: 520px; max-width: 96vw;"
    :mask-closable="!saving"
    :closable="!saving"
    @after-leave="resetForm"
  >
    <n-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-placement="left"
      label-width="100px"
      require-mark-placement="right-hanging"
    >
      <n-form-item label="Name" path="name">
        <n-input
          v-model:value="form.name"
          placeholder="Project name"
          :disabled="saving"
          @keydown.enter.prevent="submit"
        />
      </n-form-item>

      <n-form-item label="Status" path="status">
        <n-select
          v-model:value="form.status"
          :options="statusOptions"
          :disabled="saving"
        />
      </n-form-item>

      <n-form-item label="Deadline" path="deadline">
        <n-date-picker
          v-model:value="deadlineTs"
          type="date"
          clearable
          :disabled="saving"
          style="width: 100%;"
          @update:value="onDeadlineChange"
        />
      </n-form-item>

      <n-form-item label="Tags" path="tags">
        <n-dynamic-tags
          v-model:value="form.tags"
          :disabled="saving"
        />
      </n-form-item>
    </n-form>

    <template #footer>
      <n-flex justify="end" gap="8">
        <n-button :disabled="saving" @click="visible = false">Cancel</n-button>
        <n-button type="primary" :loading="saving" @click="submit">
          {{ isEdit ? 'Save Changes' : 'Create Project' }}
        </n-button>
      </n-flex>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  NModal, NForm, NFormItem, NInput, NSelect, NDatePicker,
  NDynamicTags, NButton, NFlex, useMessage,
} from 'naive-ui'
import type { FormInst, FormRules } from 'naive-ui'
import { usePmStore } from '@/stores/pm'
import type { Project } from '@/types/pm'

// ─── Props / Emits ──────────────────────────────────────────────────────────

const props = defineProps<{
  modelValue: boolean
  /** Pass a project to enter edit mode; omit for create mode */
  project?: Project | null
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', v: boolean): void
  (e: 'saved', project: Project): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: v => emit('update:modelValue', v),
})

const isEdit = computed(() => !!props.project)

// ─── Store / UI ──────────────────────────────────────────────────────────────

const store = usePmStore()
const message = useMessage()
const formRef = ref<FormInst | null>(null)
const saving = ref(false)

// ─── Form state ──────────────────────────────────────────────────────────────

interface FormModel {
  name: string
  status: 'active' | 'archived' | 'on_hold'
  deadline: string | null
  tags: string[]
}

const form = ref<FormModel>({
  name: '',
  status: 'active',
  deadline: null,
  tags: [],
})

// NDatePicker uses timestamp (ms); we convert to/from ISO date string
const deadlineTs = ref<number | null>(null)

function onDeadlineChange(ts: number | null) {
  if (ts === null) {
    form.value.deadline = null
  } else {
    form.value.deadline = new Date(ts).toISOString().slice(0, 10)
  }
}

const statusOptions = [
  { label: 'Active', value: 'active' },
  { label: 'On Hold', value: 'on_hold' },
  { label: 'Archived', value: 'archived' },
]

const rules: FormRules = {
  name: [{ required: true, message: 'Project name is required', trigger: 'blur' }],
}

// Populate form when editing
watch(
  () => props.project,
  (p) => {
    if (p) {
      form.value = {
        name: p.name,
        status: p.status,
        deadline: p.deadline,
        tags: [...(p.tags ?? [])],
      }
      deadlineTs.value = p.deadline ? new Date(p.deadline).getTime() : null
    } else {
      resetForm()
    }
  },
  { immediate: true },
)

function resetForm() {
  form.value = { name: '', status: 'active', deadline: null, tags: [] }
  deadlineTs.value = null
}

// ─── Submit ──────────────────────────────────────────────────────────────────

async function submit() {
  await formRef.value?.validate()
  saving.value = true
  try {
    let saved: Project
    if (isEdit.value && props.project) {
      saved = await store.updateProject(props.project.id, {
        name: form.value.name,
        status: form.value.status,
        deadline: form.value.deadline,
        tags: form.value.tags,
      })
      message.success('Project updated')
    } else {
      saved = await store.createProject({
        name: form.value.name,
        status: form.value.status,
        deadline: form.value.deadline,
        tags: form.value.tags,
      })
      message.success('Project created')
    }
    emit('saved', saved)
    visible.value = false
  } catch (err: unknown) {
    message.error(err instanceof Error ? err.message : 'Failed to save project')
  } finally {
    saving.value = false
  }
}
</script>

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
  <div>
    <n-h2 style="margin-bottom: 20px;">BOM Analyzer</n-h2>

    <!-- Upload card -->
    <n-card v-if="!result" title="Upload BOM Files" style="max-width: 640px;">
      <n-upload
        ref="uploadRef"
        accept=".xlsx,.xls"
        :multiple="true"
        :default-upload="false"
        @change="onFileChange"
      >
        <n-upload-dragger>
          <n-flex vertical align="center" style="padding: 24px 0; gap: 8px;">
            <n-icon :component="CloudUploadIcon" size="48" depth="3" />
            <n-text>Click or drag one or more BOM Excel files here</n-text>
            <n-text depth="3" style="font-size: 12px;">
              .xlsx / .xls · Multiple files supported
            </n-text>
          </n-flex>
        </n-upload-dragger>
      </n-upload>

      <n-flex justify="flex-end" style="margin-top: 16px;" gap="8">
        <n-button
          type="primary"
          :loading="loading"
          :disabled="selectedFiles.length === 0"
          @click="handleAnalyze"
        >
          Aggregate &amp; Analyze
        </n-button>
      </n-flex>

      <n-alert v-if="error" type="error" style="margin-top: 16px;">{{ error }}</n-alert>
    </n-card>

    <!-- Result panel -->
    <template v-else>
      <n-flex justify="space-between" align="center" style="margin-bottom: 16px;" :wrap="false">
        <n-flex vertical gap="2">
          <n-text style="font-weight: 500;">Aggregation complete</n-text>
          <n-text depth="3" style="font-size: 12px;">
            Files: {{ result.filenames.join(', ') }}
          </n-text>
        </n-flex>
        <n-flex gap="8">
          <n-button size="small" @click="downloadReport">
            <template #icon><n-icon :component="DownloadIcon" /></template>
            Download Excel
          </n-button>
          <n-button type="primary" ghost size="small" @click="reset">
            New Analysis
          </n-button>
        </n-flex>
      </n-flex>

      <!-- Suspicious items count -->
      <n-alert
        v-if="suspiciousCount > 0"
        type="warning"
        style="margin-bottom: 12px;"
      >
        {{ suspiciousCount }} suspicious item(s) detected (highlighted in yellow).
      </n-alert>

      <ReportTable
        :headers="result.report.headers"
        :rows="result.report.rows"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  NAlert, NButton, NCard, NFlex, NH2, NIcon,
  NText, NUpload, NUploadDragger,
} from 'naive-ui'
import type { UploadFileInfo } from 'naive-ui'
import { CloudUploadOutline as CloudUploadIcon, DownloadOutline as DownloadIcon } from '@vicons/ionicons5'
import client from '@/api/client'
import ReportTable from '@/components/ReportTable.vue'

type CellValue = string | number | boolean | null

interface BomRow {
  is_suspicious: boolean
  values: CellValue[]
}

interface BomReport {
  headers: string[]
  rows: BomRow[]
}

interface AnalysisResult {
  filenames: string[]
  analysis_id: string | null
  report: BomReport
}

const uploadRef = ref()
const selectedFiles = ref<File[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const result = ref<AnalysisResult | null>(null)

const suspiciousCount = computed(
  () => result.value?.report.rows.filter(r => r.is_suspicious).length ?? 0
)

function onFileChange(data: { fileList: UploadFileInfo[] }) {
  selectedFiles.value = data.fileList.map(f => f.file!).filter(Boolean)
}

async function handleAnalyze() {
  if (selectedFiles.value.length === 0) return
  loading.value = true
  error.value = null

  const form = new FormData()
  selectedFiles.value.forEach(f => form.append('bom_files', f))

  try {
    const { data } = await client.post<AnalysisResult>('/bom/analyze/', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    result.value = data
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Analysis failed'
  } finally {
    loading.value = false
  }
}

function downloadReport() {
  window.location.href = '/api/bom/download/'
}

function reset() {
  result.value = null
  selectedFiles.value = []
  error.value = null
  uploadRef.value?.clear()
}
</script>

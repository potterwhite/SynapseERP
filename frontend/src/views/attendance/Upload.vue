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
    <n-h2 style="margin-bottom: 20px;">Attendance Analyzer</n-h2>

    <!-- Upload card -->
    <n-card v-if="!result" title="Upload Attendance File" style="max-width: 600px;">
      <n-upload
        ref="uploadRef"
        accept=".xlsx,.xls"
        :max="1"
        :default-upload="false"
        @change="onFileChange"
      >
        <n-upload-dragger>
          <n-flex vertical align="center" style="padding: 24px 0; gap: 8px;">
            <n-icon :component="CloudUploadIcon" size="48" depth="3" />
            <n-text>Click or drag an Excel file here</n-text>
            <n-text depth="3" style="font-size: 12px;">.xlsx / .xls</n-text>
          </n-flex>
        </n-upload-dragger>
      </n-upload>

      <n-flex justify="flex-end" style="margin-top: 16px;" gap="8">
        <n-button
          type="primary"
          :loading="loading"
          :disabled="!selectedFile"
          @click="handleAnalyze"
        >
          Analyze
        </n-button>
      </n-flex>

      <n-alert v-if="error" type="error" style="margin-top: 16px;">{{ error }}</n-alert>
    </n-card>

    <!-- Result panel -->
    <template v-else>
      <n-flex justify="space-between" align="center" style="margin-bottom: 16px;" :wrap="false">
        <n-text><b>{{ result.filename }}</b> — analysis complete</n-text>
        <n-flex gap="8">
          <n-button size="small" @click="downloadReport('detailed', 'zh-hans')">
            <template #icon><n-icon :component="DownloadIcon" /></template>
            详细报告 (ZH)
          </n-button>
          <n-button size="small" @click="downloadReport('detailed', 'en')">
            <template #icon><n-icon :component="DownloadIcon" /></template>
            Detailed (EN)
          </n-button>
          <n-button size="small" @click="downloadReport('public', 'zh-hans')">
            公开报告
          </n-button>
          <n-button type="primary" ghost size="small" @click="reset">
            New Analysis
          </n-button>
        </n-flex>
      </n-flex>

      <n-tabs v-model:value="activeTab" type="segment" size="small" style="margin-bottom: 16px;">
        <n-tab-pane name="detailed" tab="Detailed Report" />
        <n-tab-pane name="public" tab="Public Report" />
      </n-tabs>

      <ReportTable
        :headers="activeReport.headers"
        :rows="activeReport.rows"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  NAlert, NButton, NCard, NFlex, NH2, NIcon, NTabs, NTabPane,
  NText, NUpload, NUploadDragger,
} from 'naive-ui'
import type { UploadFileInfo } from 'naive-ui'
import { CloudUploadOutline as CloudUploadIcon, DownloadOutline as DownloadIcon } from '@vicons/ionicons5'
import client from '@/api/client'
import ReportTable from '@/components/ReportTable.vue'

interface ReportData {
  headers: string[]
  rows: (string | number)[][]
}

interface AnalysisResult {
  filename: string
  analysis_id: string | null
  detailed_report: ReportData | null
  public_report: ReportData | null
}

const uploadRef = ref()
const selectedFile = ref<File | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const result = ref<AnalysisResult | null>(null)
const activeTab = ref<'detailed' | 'public'>('detailed')

const activeReport = computed<ReportData>(() => {
  const r = result.value
  if (!r) return { headers: [], rows: [] }
  return (activeTab.value === 'detailed' ? r.detailed_report : r.public_report) ?? { headers: [], rows: [] }
})

function onFileChange(data: { fileList: UploadFileInfo[] }) {
  selectedFile.value = data.fileList[0]?.file ?? null
}

async function handleAnalyze() {
  if (!selectedFile.value) return
  loading.value = true
  error.value = null

  const form = new FormData()
  form.append('excel_file', selectedFile.value)

  try {
    const { data } = await client.post<AnalysisResult>('/attendance/analyze/', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    result.value = data
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Analysis failed'
  } finally {
    loading.value = false
  }
}

function downloadReport(reportType: 'detailed' | 'public', lang: string) {
  // Opens the download endpoint directly — browser handles the file save dialog.
  // The session cookie is sent automatically (withCredentials: true on the client).
  window.location.href = `/api/attendance/download/?report_type=${reportType}&lang=${lang}`
}

function reset() {
  result.value = null
  selectedFile.value = null
  error.value = null
  uploadRef.value?.clear()
}
</script>

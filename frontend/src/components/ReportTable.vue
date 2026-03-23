<!--
  ReportTable.vue — generic table renderer for Attendance / BOM analysis results.
  Accepts flat headers + rows arrays from the API.
-->
<template>
  <div class="report-table-wrapper">
    <n-data-table
      :columns="columns"
      :data="tableData"
      :pagination="rows.length > 20 ? { pageSize: 20 } : false"
      :row-class-name="(row: RowRecord) => row.__suspicious ? 'row-suspicious' : ''"
      size="small"
      striped
      bordered
      :scroll-x="scrollWidth"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, h } from 'vue'
import { NDataTable } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'

type CellValue = string | number | boolean | null

interface RowRecord {
  __suspicious: boolean
  [key: string]: CellValue
}

const props = defineProps<{
  headers: string[]
  rows: ({ is_suspicious?: boolean; values: CellValue[] } | CellValue[])[]
}>()

// Flatten rows into objects keyed by header
const tableData = computed<RowRecord[]>(() =>
  props.rows.map(row => {
    const isSuspicious = !Array.isArray(row) && (row.is_suspicious ?? false)
    const values: CellValue[] = Array.isArray(row) ? row : row.values
    const record: RowRecord = { __suspicious: isSuspicious }
    props.headers.forEach((h, i) => {
      record[h] = values[i] ?? null
    })
    return record
  })
)

const columns = computed<DataTableColumns<RowRecord>>(() =>
  props.headers.map(header => ({
    title: header,
    key: header,
    ellipsis: { tooltip: true },
    minWidth: 80,
    render(row: RowRecord) {
      const val = row[header]
      // Convert newline chars in text cells to line breaks for display
      if (typeof val === 'string' && val.includes('\n')) {
        return h('div', { style: 'white-space: pre-line; line-height: 1.5;' }, val)
      }
      return val as string
    },
  }))
)

// Make the table horizontally scrollable if many columns
const scrollWidth = computed(() =>
  props.headers.length > 6 ? props.headers.length * 140 : undefined
)
</script>

<style scoped>
.report-table-wrapper {
  overflow: auto;
}
</style>

<style>
/* Highlight suspicious BOM rows */
.n-data-table .row-suspicious td {
  background-color: #fff3cd !important;
}
</style>

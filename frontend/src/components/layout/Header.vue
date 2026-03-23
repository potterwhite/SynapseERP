<template>
  <n-layout-header bordered style="height: 64px; padding: 0 24px; display: flex; align-items: center; justify-content: space-between;">
    <span style="font-size: 18px; font-weight: 600;">SynapseERP</span>
    <n-space>
      <n-text depth="3" style="font-size: 13px;">v0.9.0-alpha</n-text>
    </n-space>
  </n-layout-header>
</template>

<script setup lang="ts">
import { NLayoutHeader, NSpace, NText } from 'naive-ui'

defineEmits<{ (e: 'toggle-sidebar'): void }>()
</script>

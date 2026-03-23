<template>
  <!-- When ?project=<id> is present, show the project task view;
       otherwise show the project list. -->
  <ProjectTaskView v-if="hasProject" />
  <ProjectList v-else />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import ProjectList from './ProjectList.vue'
import ProjectTaskView from './ProjectTaskView.vue'

const route = useRoute()
const hasProject = computed(() => Boolean(route.query.project))
</script>

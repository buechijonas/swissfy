<template>
  <div class="breadcrumbs text-sm">
    <ul>
      <li v-for="item in items" :key="item.label" class="text-app-muted">
        <RouterLink v-if="item.to" :to="item.to">{{ item.label }}</RouterLink>
        <span v-else>{{ item.label }}</span>
      </li>
    </ul>
  </div>
</template>

<script>
import { RouterLink } from 'vue-router'

export default {
  name: 'BreadcrumbTrail',
  components: { RouterLink },
  props: {
    items: { type: Array, required: true },
  },
}
</script>

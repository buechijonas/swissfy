<template>
  <div class="flex min-h-12 items-center px-6 pt-4">
    <div class="breadcrumbs text-sm">
      <ul>
        <li v-for="(item, index) in items" :key="index" class="text-docs-muted">
          <RouterLink v-if="item.to" :to="item.to">{{ item.label }}</RouterLink>
          <span v-else>{{ item.label }}</span>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
import { RouterLink } from 'vue-router'

export default {
  name: 'BaseBreadcrumbs',
  components: { RouterLink },
  props: {
    items: { type: Array, required: true },
  },
}
</script>

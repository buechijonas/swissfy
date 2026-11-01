<template>
  <div
    class="app-header max-lg:hidden sticky top-0 z-10 bg-base-200 flex items-center justify-between gap-4 border-b border-swissfy-border py-2 px-6"
  >
    <div class="breadcrumbs text-sm">
      <ul>
        <li class="text-swissfy-muted" v-for="(item, index) in items" :key="index">
          <RouterLink v-if="item.to" :to="item.to">
            {{ item.label }}
          </RouterLink>

          <span v-else>
            {{ item.label }}
          </span>
        </li>
      </ul>
    </div>
    <slot name="actions" />
  </div>
</template>

<script>
import { RouterLink } from 'vue-router'

export default {
  name: 'BaseBreadcrumbs',
  components: { RouterLink },
  props: {
    items: {
      type: Array,
      required: true,
    },
  },
}
</script>

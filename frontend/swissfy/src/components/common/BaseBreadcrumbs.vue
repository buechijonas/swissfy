<template>
  <div
    class="app-header sticky top-0 z-10 flex items-center justify-between gap-4 border-b border-app-border bg-base-200 px-6 py-2 max-lg:hidden"
  >
    <BreadcrumbTrail :items="items" />
    <slot name="actions" />
  </div>
</template>

<script>
import BreadcrumbTrail from '@core/components/BreadcrumbTrail.vue'

export default {
  name: 'BaseBreadcrumbs',
  components: { BreadcrumbTrail },
  props: {
    items: { type: Array, required: true },
  },
}
</script>

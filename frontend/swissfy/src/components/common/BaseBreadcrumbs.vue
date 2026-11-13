<template>
  <div
    class="app-header max-lg:hidden sticky top-0 z-10 bg-base-200 flex items-center justify-between gap-4 border-b border-app-border py-2 px-6"
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

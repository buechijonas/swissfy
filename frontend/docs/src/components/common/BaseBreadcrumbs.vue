<template>
  <div class="flex min-h-12 items-center px-6 pt-4">
    <BreadcrumbTrail :items="items" />
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

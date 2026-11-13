<template>
  <BaseBreadcrumbs v-if="breadcrumbs.length" :items="breadcrumbs" />
  <div class="flex flex-1 flex-col gap-6 px-6 pt-4 pb-16">
    <ErrorText :message="error" />
    <div v-if="loading" class="flex max-w-200 flex-col gap-4">
      <div v-for="n in 3" :key="n" class="skeleton h-32"></div>
    </div>
    <slot v-else />
  </div>
</template>

<script>
import ErrorText from '@core/components/ErrorText.vue'
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'

export default {
  name: 'DocsPage',
  components: { BaseBreadcrumbs, ErrorText },
  props: {
    breadcrumbs: { type: Array, default: () => [] },
    loading: { type: Boolean, default: false },
    error: { type: String, default: '' },
  },
}
</script>

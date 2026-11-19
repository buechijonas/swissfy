<template>
  <div class="flex max-h-[calc(100dvh-var(--header-height))] flex-col lg:max-h-full">
    <BaseBreadcrumbs :items="breadcrumbs" />
    <div class="flex min-h-0 flex-1 flex-col overflow-y-auto px-6 pb-16">
      <div class="mx-auto w-full max-w-100">
        <div
          class="list mt-16 rounded-box border-1 border-solid border-app-border bg-base-100 p-8 shadow-none max-sm:-mx-6 max-sm:rounded-none max-sm:border-x-0"
        >
          <h2 class="mb-6 text-xl font-light">{{ title }}</h2>
          <div class="text-swissfy-slate">
            <slot />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'

export default {
  name: 'AuthPage',
  components: { BaseBreadcrumbs },
  props: {
    title: { type: String, required: true },
    breadcrumbLabel: { type: String, default: null },
  },
  computed: {
    breadcrumbs() {
      return [{ label: this.breadcrumbLabel ?? this.title, to: '/' }]
    },
  },
}
</script>

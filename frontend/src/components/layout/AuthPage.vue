<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div class="flex flex-col pb-16 px-6 max-h-[calc(100dvh-101px)] overflow-y-auto">
    <div class="mx-auto w-full max-w-100">
      <div
        class="list bg-base-100 rounded-box shadow-none border-swissfy-border border-solid border-1 mt-16 p-8"
      >
        <h2 class="text-xl font-light mb-6">{{ title }}</h2>
        <div class="text-swissfy-slate">
          <slot />
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

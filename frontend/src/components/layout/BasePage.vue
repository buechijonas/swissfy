<template>
  <div class="relative grid min-h-[100dvh] grid-cols-[8px_auto_1fr]">
    <div class="app-nav-accent absolute top-0 left-0 z-20 h-full w-2 bg-primary" />
    <BaseNavigation :active-navigation="activeNavigation" />
    <div class="col-start-3 row-start-1 flex min-w-0 flex-col bg-base-200">
      <BaseHeader />
      <div
        ref="scrollArea"
        class="flex flex-1 flex-col lg:flex-none lg:h-[calc(100dvh-48px)] lg:overflow-y-auto"
      >
        <slot />
      </div>
    </div>
  </div>
</template>

<script>
import BaseNavigation from '@/components/common/BaseNavigation.vue'
import BaseHeader from '@/components/common/BaseHeader.vue'

export default {
  name: 'BasePage',
  components: { BaseNavigation, BaseHeader },
  props: {
    activeNavigation: {
      type: String,
      default: null,
    },
  },
  watch: {
    $route() {
      if (this.$refs.scrollArea) this.$refs.scrollArea.scrollTop = 0
    },
  },
}
</script>

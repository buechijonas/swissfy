<template>
  <div
    class="flex flex-col lg:gap-8 overflow-y-auto max-lg:h-[calc(100dvh-48px)] lg:max-h-none lg:overflow-y-visible lg:flex-1"
  >
    <div class="mx-auto w-full max-w-150 px-6 lg:flex-1">
      <h2 class="text-xl font-light my-4">{{ title }}</h2>
      <div
        class="list bg-base-100 rounded-box shadow-none border-swissfy-border border-solid border-1 p-8"
      >
        <div class="text-swissfy-slate">
          <slot />
        </div>
      </div>
    </div>
    <BaseFooter />
  </div>
</template>

<script>
import BaseFooter from '@/components/common/BaseFooter.vue'

export default {
  name: 'LegalPage',
  components: { BaseFooter },
  props: {
    title: { type: String, required: true },
  },
}
</script>

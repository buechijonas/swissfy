<template>
  <BaseCard
    class="flex flex-col items-center gap-4 p-6 text-center sm:flex-row sm:items-center sm:justify-between sm:text-left"
  >
    <div class="min-w-0">
      <p>{{ title }}</p>
      <p v-if="hint" class="mt-1 text-sm text-app-muted">{{ hint }}</p>
    </div>
    <slot />
  </BaseCard>
</template>

<script>
import BaseCard from '@core/components/BaseCard.vue'

export default {
  name: 'SettingCard',
  components: { BaseCard },
  props: {
    title: { type: String, required: true },
    hint: { type: String, default: null },
  },
}
</script>

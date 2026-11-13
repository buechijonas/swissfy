<template>
  <BaseCard
    class="p-6 flex flex-col items-center text-center gap-4 sm:flex-row sm:items-center sm:text-left sm:justify-between"
  >
    <div class="min-w-0">
      <p>{{ title }}</p>
      <p v-if="hint" class="text-app-muted text-sm mt-1">{{ hint }}</p>
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

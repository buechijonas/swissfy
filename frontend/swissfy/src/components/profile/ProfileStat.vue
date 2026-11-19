<template>
  <div class="flex flex-col items-center gap-2">
    <RouterLink v-if="visible" :to="to" class="flex flex-col items-center gap-2 hover:underline">
      <span class="text-xl font-bold">{{ count }}</span>
      <span class="text-sm text-app-muted">{{ label }}</span>
    </RouterLink>
    <template v-else>
      <CipherText class="text-xl font-bold" />
      <span class="text-sm text-app-muted">{{ label }}</span>
    </template>
    <slot />
  </div>
</template>

<script>
import { RouterLink } from 'vue-router'
import CipherText from '@/components/common/CipherText.vue'

export default {
  name: 'ProfileStat',
  components: { CipherText, RouterLink },
  props: {
    count: { type: Number, default: null },
    label: { type: String, required: true },
    to: { type: String, required: true },
    visible: { type: Boolean, required: true },
  },
}
</script>

<template>
  <span
    role="img"
    :aria-label="alt || null"
    :aria-hidden="alt ? null : 'true'"
    class="app-icon inline-block shrink-0 bg-current"
    :class="size === 'sm' ? 'size-3' : 'size-4'"
    :style="{ maskImage }"
  />
</template>

<script>
import { icons } from '@/assets/icons'

export default {
  name: 'AppIcon',
  props: {
    name: { type: String, required: true },
    alt: { type: String, default: '' },
    size: { type: String, default: 'md' },
  },
  computed: {
    maskImage() {
      return `url("${icons[this.name]}")`
    },
  },
}
</script>

<style scoped>
.app-icon {
  mask-repeat: no-repeat;
  mask-position: center;
  mask-size: contain;
}
</style>

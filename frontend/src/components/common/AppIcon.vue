<template>
  <span
    role="img"
    :aria-label="alt || null"
    :aria-hidden="alt ? null : 'true'"
    class="app-icon inline-block shrink-0"
    :class="[
      size === 'sm' ? 'size-3' : 'size-4',
      { 'bg-current': !y2kIcon, 'opacity-50 grayscale': faded },
    ]"
    :style="style"
  />
</template>

<script>
import { icons, y2kIcons } from '@/assets/icons'
import { design } from '@/lib/preferences.js'

const FADED = ['heart', 'bookmark', 'unlock']

export default {
  name: 'AppIcon',
  props: {
    name: { type: String, required: true },
    alt: { type: String, default: '' },
    size: { type: String, default: 'md' },
  },
  computed: {
    y2kIcon() {
      return design.value === 'y2k' ? y2kIcons[this.name] : null
    },
    faded() {
      return Boolean(this.y2kIcon) && FADED.includes(this.name)
    },
    style() {
      if (this.y2kIcon) return { backgroundImage: `url("${this.y2kIcon}")` }
      return { maskImage: `url("${icons[this.name]}")` }
    },
  },
}
</script>

<style scoped>
.app-icon {
  mask-repeat: no-repeat;
  mask-position: center;
  mask-size: contain;
  background-repeat: no-repeat;
  background-position: center;
  background-size: contain;
}
</style>

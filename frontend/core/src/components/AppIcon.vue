<template>
  <span
    role="img"
    :aria-label="alt || null"
    :aria-hidden="alt ? null : 'true'"
    class="app-icon inline-block shrink-0"
    :class="[size === 'sm' ? 'size-3' : 'size-4', icon.class]"
    :style="icon.style"
  />
</template>

<script>
export default {
  name: 'AppIcon',
  inject: {
    iconSource: { default: () => () => ({ class: 'bg-current', style: {} }) },
  },
  props: {
    name: { type: String, required: true },
    alt: { type: String, default: '' },
    size: { type: String, default: 'md' },
  },
  computed: {
    icon() {
      return this.iconSource(this.name)
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

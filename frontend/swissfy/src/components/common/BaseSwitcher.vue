<template>
  <div ref="list" class="app-switcher relative flex" :class="{ 'is-vertical flex-col': vertical }">
    <span
      v-if="bubble"
      ref="bubble"
      class="app-bubble"
      :style="
        vertical
          ? { top: `${bubble.top}px`, height: `${bubble.height}px` }
          : { left: `${bubble.left}px`, width: `${bubble.width}px` }
      "
    />
    <BaseButton
      v-for="option in options"
      :key="String(option.value)"
      ref="buttons"
      type="button"
      class="relative shrink-0"
      :class="itemClass"
      :size="size"
      :variant="active === option.value ? 'primary' : 'neutral'"
      :disabled="disabled"
      :aria-pressed="active === option.value"
      @click="$emit('select', option.value)"
    >
      <AppIcon :name="option.icon" />
      {{ option.label }}
    </BaseButton>
  </div>
</template>

<script>
import AppIcon from '@/components/common/AppIcon.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import { wobble } from '@/lib/bubble.js'

export default {
  name: 'BaseSwitcher',
  components: { AppIcon, BaseButton },
  props: {
    options: { type: Array, required: true },
    active: { type: [String, Boolean], required: true },
    size: { type: String, default: 'md' },
    disabled: { type: Boolean, default: false },
    vertical: { type: Boolean, default: false },
    itemClass: { type: [String, Array, Object], default: '' },
  },
  emits: ['select'],
  data() {
    return {
      bubble: null,
      observer: null,
    }
  },
  computed: {
    activeIndex() {
      return this.options.findIndex((option) => option.value === this.active)
    },
  },
  watch: {
    activeIndex() {
      this.$nextTick(() => {
        this.placeBubble()
        wobble(this.$refs.bubble)
      })
    },
  },
  mounted() {
    this.placeBubble()
    this.observer = new ResizeObserver(() => this.placeBubble())
    this.observer.observe(this.$refs.list)
  },
  beforeUnmount() {
    this.observer.disconnect()
  },
  methods: {
    placeBubble() {
      const button = this.$refs.buttons?.[this.activeIndex]?.$el
      this.bubble = button && {
        left: button.offsetLeft,
        width: button.offsetWidth,
        top: button.offsetTop,
        height: button.offsetHeight,
      }
    },
  },
}
</script>

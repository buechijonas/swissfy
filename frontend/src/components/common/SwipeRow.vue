<template>
  <div
    class="relative overflow-hidden touch-pan-y"
    @touchstart.passive="start"
    @touchmove.passive="move"
    @touchend="end"
    @touchcancel="reset"
    @click.capture="suppressClick"
  >
    <div
      class="absolute inset-0 flex items-center justify-end gap-2 px-6 bg-primary text-primary-content font-bold"
      :class="{ 'opacity-60': !armed }"
    >
      <AppIcon :name="icon" />
      <span>{{ label }}</span>
    </div>
    <div
      class="relative bg-base-100"
      :class="{ 'transition-transform': direction !== 'horizontal' }"
      :style="{ transform: `translateX(${offset}px)` }"
    >
      <slot />
    </div>
  </div>
</template>

<script>
import AppIcon from '@/components/common/AppIcon.vue'

const DIRECTION_THRESHOLD = 8
const ACTION_THRESHOLD = 96

export default {
  name: 'SwipeRow',
  components: { AppIcon },
  props: {
    icon: { type: String, required: true },
    label: { type: String, required: true },
  },
  emits: ['action'],
  data() {
    return {
      offset: 0,
      direction: null,
      swiped: false,
    }
  },
  computed: {
    armed() {
      return this.offset <= -ACTION_THRESHOLD
    },
  },
  methods: {
    start(event) {
      const touch = event.touches[0]
      this.startX = touch.clientX
      this.startY = touch.clientY
      this.direction = null
      this.swiped = false
    },
    move(event) {
      const touch = event.touches[0]
      const dx = touch.clientX - this.startX
      const dy = touch.clientY - this.startY
      if (!this.direction) {
        if (Math.max(Math.abs(dx), Math.abs(dy)) < DIRECTION_THRESHOLD) return
        this.direction = Math.abs(dx) > Math.abs(dy) ? 'horizontal' : 'vertical'
      }
      if (this.direction === 'horizontal') {
        this.offset = Math.max(Math.min(0, dx), -this.$el.clientWidth)
      }
    },
    end() {
      if (this.direction === 'horizontal') this.swiped = true
      if (this.armed) this.$emit('action')
      this.reset()
    },
    reset() {
      this.offset = 0
      this.direction = null
    },
    suppressClick(event) {
      if (!this.swiped) return
      this.swiped = false
      event.preventDefault()
      event.stopPropagation()
    },
  },
}
</script>

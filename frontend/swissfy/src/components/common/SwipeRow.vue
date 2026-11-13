<template>
  <div
    v-swipe="{ direction: setDirection, move, end, cancel: reset }"
    class="relative overflow-hidden touch-pan-y"
  >
    <div
      v-show="offset"
      class="absolute inset-0 flex items-center justify-end gap-2 px-6 bg-primary text-primary-content font-bold"
      :class="{ 'opacity-60': !armed }"
    >
      <AppIcon :name="icon" />
      <span>{{ label }}</span>
    </div>
    <div
      class="app-swipe-row relative bg-base-100"
      :class="{ 'transition-transform': direction !== 'horizontal', 'is-swiping': offset }"
      :style="{ transform: `translateX(${offset}px)` }"
    >
      <slot />
    </div>
  </div>
</template>

<script>
import clamp from 'lodash-es/clamp'
import AppIcon from '@core/components/AppIcon.vue'
import swipe from '@/directives/swipe.js'

const ACTION_THRESHOLD = 96

export default {
  name: 'SwipeRow',
  components: { AppIcon },
  directives: { swipe },
  props: {
    icon: { type: String, required: true },
    label: { type: String, required: true },
  },
  emits: ['action'],
  data() {
    return {
      offset: 0,
      direction: null,
    }
  },
  computed: {
    armed() {
      return this.offset <= -ACTION_THRESHOLD
    },
  },
  methods: {
    setDirection(direction) {
      this.direction = direction
    },
    move(dx, width) {
      this.offset = clamp(dx, -width, 0)
    },
    end() {
      if (this.armed) this.$emit('action')
      this.reset()
    },
    reset() {
      this.offset = 0
      this.direction = null
    },
  },
}
</script>

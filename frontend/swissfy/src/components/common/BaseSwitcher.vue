<template>
  <div class="app-switcher relative flex" :class="{ 'is-vertical flex-col': vertical }">
    <span v-if="bubble" v-wobble="wobbles" class="app-bubble" :style="bubbleStyle" />
    <BaseButton
      v-for="option in options"
      :key="String(option.value)"
      v-bounds="(box) => storeBox(option.value, box)"
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
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import bounds from '@/directives/bounds.js'
import wobble from '@/directives/wobble.js'

export default {
  name: 'BaseSwitcher',
  components: { AppIcon, BaseButton },
  directives: { bounds, wobble },
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
      boxes: {},
      wobbles: 0,
    }
  },
  computed: {
    bubble() {
      return this.boxes[this.active] ?? null
    },
    bubbleStyle() {
      const { left, top, width, height } = this.bubble
      if (this.vertical) return { top: `${top}px`, height: `${height}px` }
      return { left: `${left}px`, width: `${width}px` }
    },
  },
  watch: {
    active() {
      this.wobbles += 1
    },
  },
  methods: {
    storeBox(value, box) {
      this.boxes[value] = box
    },
  },
}
</script>

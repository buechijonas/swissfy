<template>
  <button
    type="button"
    class="select select-sm w-48 gap-2 bg-base-100 text-left"
    :disabled="disabled"
    :aria-label="label"
    :aria-expanded="isOpen"
    aria-haspopup="listbox"
    @click="toggle"
    @keydown.esc="close"
  >
    <AppIcon :name="current?.icon ?? icon" />
    <span class="truncate">{{ current?.label }}</span>
  </button>
  <Teleport to="body">
    <div
      v-if="isOpen"
      class="fixed inset-0 z-50"
      @click="close"
      @wheel.passive="close"
      @touchmove.passive="close"
    ></div>
    <ul
      v-if="isOpen"
      role="listbox"
      :aria-label="label"
      :style="position"
      class="app-menu menu fixed z-50 w-56 rounded-box border border-app-border bg-base-100 p-1 text-base-content [--depth:0] [--menu-active-bg:transparent] [--menu-active-fg:var(--color-base-content)] [&_li>*:hover]:[--menu-active-bg:color-mix(in_oklab,var(--color-base-content)_10%,transparent)]"
      @keydown.esc="close"
    >
      <li v-for="option in options" :key="String(option.value)">
        <button
          type="button"
          role="option"
          :aria-selected="option.value === modelValue"
          :lang="option.lang"
          class="flex h-12 items-center gap-3"
          :class="{ 'font-bold': option.value === modelValue }"
          @click="choose(option.value)"
        >
          <AppIcon :name="option.icon ?? icon" class="size-6!" />
          <span class="flex-1">{{ option.label }}</span>
          <AppIcon name="check" :class="{ invisible: option.value !== modelValue }" />
        </button>
      </li>
    </ul>
  </Teleport>
</template>

<script>
import AppIcon from '@core/components/AppIcon.vue'

const GAP = 8

export default {
  name: 'SelectMenu',
  components: { AppIcon },
  props: {
    modelValue: { type: [String, Boolean, Number], default: null },
    options: { type: Array, required: true },
    label: { type: String, required: true },
    icon: { type: String, default: 'check' },
    disabled: { type: Boolean, default: false },
  },
  emits: ['update:modelValue'],
  data() {
    return { isOpen: false, position: {} }
  },
  computed: {
    current() {
      return this.options.find((option) => option.value === this.modelValue)
    },
  },
  methods: {
    toggle(event) {
      const box = event.currentTarget.getBoundingClientRect()
      this.position = {
        top: `${box.bottom + GAP}px`,
        right: `${document.documentElement.clientWidth - box.right}px`,
      }
      this.isOpen = !this.isOpen
    },
    close() {
      this.isOpen = false
    },
    choose(value) {
      this.close()
      if (value !== this.modelValue) this.$emit('update:modelValue', value)
    },
  },
}
</script>

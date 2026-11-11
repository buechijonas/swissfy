<template>
  <button :type="type" :class="classes">
    <slot />
  </button>
</template>

<script>
const VARIANT_CLASSES = {
  neutral: '',
  primary: 'btn-primary',
}

const SIZE_CLASSES = {
  sm: 'btn-sm',
  md: '',
}

export default {
  name: 'BaseButton',
  props: {
    variant: { type: String, default: 'neutral' },
    size: { type: String, default: 'md' },
    type: { type: String, default: 'button' },
  },
  computed: {
    classes() {
      return ['btn', 'shadow-none', 'gap-2', VARIANT_CLASSES[this.variant], SIZE_CLASSES[this.size]]
    },
  },
}
</script>

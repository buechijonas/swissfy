<template>
  <a v-if="url(href)" :href="url(href)" :target="target" :rel="rel" :class="classes">
    <slot />
  </a>
  <RouterLink v-else-if="to" :to="to" :class="classes">
    <slot />
  </RouterLink>
  <label v-else-if="accept" :class="[classes, { 'btn-disabled': disabled }]">
    <input
      v-files="(files) => $emit('files', files)"
      type="file"
      :accept="accept"
      :disabled="disabled"
      class="sr-only"
    />
    <slot />
  </label>
  <button v-else :type="type" :disabled="disabled" :class="classes">
    <slot />
  </button>
</template>

<script>
import { RouterLink } from 'vue-router'
import files from '@core/directives/files.js'
import { url } from '@core/lib/link.js'

const VARIANT_CLASSES = {
  neutral: '',
  primary: 'btn-primary',
  ghost: 'btn-ghost',
  error: 'btn-error',
}

const SIZE_CLASSES = {
  xs: 'btn-xs',
  sm: 'btn-sm',
  md: '',
}

const SHAPE_CLASSES = {
  circle: 'btn-circle',
  square: 'btn-square',
}

export default {
  name: 'BaseButton',
  components: { RouterLink },
  directives: { files },
  props: {
    variant: { type: String, default: 'neutral' },
    outline: { type: Boolean, default: false },
    size: { type: String, default: 'md' },
    shape: { type: String, default: null },
    block: { type: Boolean, default: false },
    to: { type: [String, Object], default: null },
    href: { type: String, default: null },
    target: { type: String, default: null },
    rel: { type: String, default: null },
    type: { type: String, default: 'button' },
    disabled: { type: Boolean, default: false },
    accept: { type: String, default: null },
  },
  emits: ['files'],
  computed: {
    classes() {
      return [
        'btn',
        'shadow-none',
        'gap-2',
        VARIANT_CLASSES[this.variant],
        this.outline ? 'btn-outline' : '',
        SIZE_CLASSES[this.size],
        this.shape ? SHAPE_CLASSES[this.shape] : '',
        this.block ? 'w-full' : '',
      ]
    },
  },
  methods: {
    url,
  },
}
</script>

<template>
  <component
    :is="tag"
    class="app-surface bg-base-100 shadow-none border-app-border border-solid border-1"
    :class="{ 'max-sm:-mx-6 max-sm:border-x-0': !inset }"
  >
    <slot />
  </component>
</template>

<script>
export default {
  name: 'BaseCard',
  props: {
    tag: { type: String, default: 'div' },
    inset: { type: Boolean, default: false },
  },
}
</script>

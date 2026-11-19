<template>
  <component
    :is="tag"
    class="app-surface border-1 border-solid border-app-border bg-base-100 shadow-none"
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

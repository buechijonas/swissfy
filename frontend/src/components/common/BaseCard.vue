<template>
  <component
    :is="tag"
    class="bg-base-100 shadow-none border-swissfy-border border-solid border-1 max-sm:-mx-6 max-sm:border-x-0"
  >
    <slot />
  </component>
</template>

<script>
export default {
  name: 'BaseCard',
  props: {
    tag: { type: String, default: 'div' },
  },
}
</script>

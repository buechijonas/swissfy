<template>
  <component :is="tag" class="border-1 border-solid border-docs-border bg-base-100 shadow-none">
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

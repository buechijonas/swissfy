<template>
  <p v-if="message" class="text-error text-sm">{{ message }}</p>
</template>

<script>
export default {
  name: 'ErrorText',
  props: {
    message: { type: String, default: null },
  },
}
</script>

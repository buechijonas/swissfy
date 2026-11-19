<template>
  <p v-if="message" class="text-sm text-error">{{ message }}</p>
</template>

<script>
export default {
  name: 'ErrorText',
  props: {
    message: { type: String, default: null },
  },
}
</script>

<template>
  <template v-for="part in parts" :key="part.start">
    <a
      v-if="part.href"
      :href="part.href"
      class="link text-primary"
      :target="part.external ? '_blank' : null"
      :rel="part.external ? 'noopener noreferrer' : null"
      >{{ part.text }}</a
    >
    <template v-else>{{ part.text }}</template>
  </template>
</template>

<script>
import { linkParts } from '@core/lib/linkify.js'

export default {
  name: 'LinkedText',
  props: {
    text: { type: String, required: true },
  },
  computed: {
    parts() {
      return linkParts(this.text)
    },
  },
}
</script>

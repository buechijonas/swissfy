<template>
  <p>
    <template v-for="part in parts" :key="part.start">
      <RouterLink
        v-if="part.hashtag"
        :to="hashtagLink(part.hashtag)"
        @click.stop
        class="pointer-events-auto font-semibold text-primary hover:underline"
        >{{ part.text }}</RouterLink
      >
      <template v-else>{{ part.text }}</template>
    </template>
  </p>
</template>

<script>
import { RouterLink } from 'vue-router'
import { hashtagLink } from '@/lib/hashtags.js'

export default {
  name: 'PostText',
  components: { RouterLink },
  props: {
    parts: { type: Array, required: true },
  },
  methods: {
    hashtagLink,
  },
}
</script>

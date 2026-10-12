<template>
  <p>
    <template v-for="(part, index) in parts" :key="index">
      <RouterLink
        v-if="part.hashtag"
        :to="hashtagLink(part.hashtag)"
        class="pointer-events-auto font-semibold text-primary hover:underline"
        >{{ part.text }}</RouterLink
      >
      <template v-else>{{ part.text }}</template>
    </template>
  </p>
</template>

<script>
import { RouterLink } from 'vue-router'
import { hashtagLink, splitHashtags } from '@/lib/hashtags.js'

export default {
  name: 'PostText',
  components: { RouterLink },
  props: {
    text: { type: String, required: true },
  },
  computed: {
    parts() {
      return splitHashtags(this.text)
    },
  },
  methods: {
    hashtagLink,
  },
}
</script>

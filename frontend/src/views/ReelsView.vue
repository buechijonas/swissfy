<template>
  <ReelFeed :key="$route.fullPath" :url="url" :empty-text="emptyText" />
  <BaseFooter dark />
</template>

<script>
import BaseFooter from '@/components/common/BaseFooter.vue'
import ReelFeed from '@/components/posts/ReelFeed.vue'

export default {
  name: 'ReelsView',
  components: { BaseFooter, ReelFeed },
  computed: {
    url() {
      const { username, name, id } = this.$route.params
      if (username) return `/api/posts/users/${encodeURIComponent(username)}/?videos=1&from=${id}`
      if (name) return `/api/posts/hashtags/${encodeURIComponent(name)}/posts/?videos=1&from=${id}`
      return '/api/posts/reels/'
    },
    emptyText() {
      return this.$route.params.id
        ? 'Noch keine Seeds.'
        : 'Noch keine Seeds von Leuten oder Hashtags, denen du folgst.'
    },
  },
}
</script>

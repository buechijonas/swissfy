<template>
  <ReelFeed :key="$route.fullPath" :url="url" :empty-text="emptyText" />
  <BaseFooter dark />
</template>

<script>
import BaseFooter from '@/components/common/BaseFooter.vue'
import ReelFeed from '@/components/posts/ReelFeed.vue'
import postsApi from '@/api/posts.js'

export default {
  name: 'ReelsView',
  components: { BaseFooter, ReelFeed },
  computed: {
    url() {
      const { username, name, id } = this.$route.params
      if (username) return postsApi.userPostsUrl(username, { videos: 1, from: id })
      if (name) return postsApi.hashtagPostsUrl(name, { videos: 1, from: id })
      return postsApi.reelsUrl()
    },
    emptyText() {
      return this.$route.params.id
        ? 'Noch keine Seeds.'
        : 'Noch keine Seeds von Leuten oder Hashtags, denen du folgst.'
    },
  },
}
</script>

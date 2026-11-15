<template>
  <div
    class="h-[calc(100dvh-var(--reel-chrome-height))] snap-y snap-mandatory overflow-y-auto bg-black lg:h-[calc(100dvh-48px)]"
  >
    <section
      v-for="post in posts"
      :key="post.id"
      class="flex h-full snap-start snap-always items-center justify-center"
    >
      <PostCard :post="post" detail reel @update="replace" @deleted="remove" />
    </section>

    <div v-if="loading" class="flex h-full items-center justify-center">
      <span class="loading loading-spinner text-white"></span>
    </div>
    <div
      v-else-if="!posts.length || error"
      class="flex h-full items-center justify-center px-6 text-center text-white/70"
    >
      {{ error || emptyTextOrDefault }}
    </div>
    <div v-intersect.ahead="onSentinel" class="h-px"></div>
  </div>
</template>

<script>
import reject from 'lodash-es/reject'
import PostCard from '@/components/posts/PostCard.vue'
import intersect from '@/directives/intersect.js'
import postFeedMixin from '@/mixins/postFeedMixin.js'
import { t } from '@/i18n.js'

export default {
  name: 'ReelFeed',
  components: { PostCard },
  directives: { intersect },
  mixins: [postFeedMixin],
  props: {
    url: { type: String, default: null },
    initialPosts: { type: Array, default: () => [] },
    emptyText: { type: String, default: null },
  },
  emits: ['deleted'],
  data() {
    return {
      posts: [...this.initialPosts],
      hasMore: Boolean(this.url),
    }
  },
  computed: {
    emptyTextOrDefault() {
      return this.emptyText ?? t('reels.empty')
    },
    loadError() {
      return t('reels.loadFailed')
    },
  },
  methods: {
    remove(id) {
      this.posts = reject(this.posts, { id })
      this.$emit('deleted', id)
    },
  },
}
</script>

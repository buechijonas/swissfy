<template>
  <div
    class="h-[calc(100dvh-var(--reel-chrome-height))] snap-y snap-mandatory overflow-y-auto bg-black lg:h-[calc(100dvh-48px)]"
  >
    <section
      v-for="post in feed.posts"
      :key="post.id"
      class="flex h-full snap-start snap-always items-center justify-center"
    >
      <PostCard :post="post" detail reel @update="feed.replace" @deleted="remove" />
    </section>

    <div v-if="feed.loading" class="flex h-full items-center justify-center">
      <span class="loading loading-spinner text-white"></span>
    </div>
    <div
      v-else-if="!feed.posts.length || feed.error"
      class="flex h-full items-center justify-center px-6 text-center text-white/70"
    >
      {{ feed.error || emptyTextOrDefault }}
    </div>
    <div v-intersect.ahead="feed.onSentinel" class="h-px"></div>
  </div>
</template>

<script>
import PostCard from '@/components/posts/PostCard.vue'
import { usePostFeed } from '@/composables/postFeed.js'
import intersect from '@/directives/intersect.js'
import { t } from '@/i18n.js'

export default {
  name: 'ReelFeed',
  components: { PostCard },
  directives: { intersect },
  props: {
    url: { type: String, default: null },
    initialPosts: { type: Array, default: () => [] },
    emptyText: { type: String, default: null },
  },
  emits: ['deleted'],
  data() {
    return {
      feed: usePostFeed({
        url: () => this.url,
        loadError: () => t('reels.loadFailed'),
        initial: this.initialPosts,
      }),
    }
  },
  computed: {
    emptyTextOrDefault() {
      return this.emptyText ?? t('reels.empty')
    },
  },
  methods: {
    remove(id) {
      this.feed.remove({ id })
      this.$emit('deleted', id)
    },
  },
}
</script>

<template>
  <div
    ref="scroller"
    class="h-[calc(100dvh-var(--mobile-chrome-height))] snap-y snap-mandatory overflow-y-auto bg-black lg:h-[calc(100dvh-48px)]"
  >
    <section
      v-for="post in posts"
      :key="post.id"
      class="flex h-full snap-start snap-always items-center justify-center"
    >
      <PostCard :post="post" detail reel @deleted="remove" />
    </section>

    <div v-if="loading" class="flex h-full items-center justify-center">
      <span class="loading loading-spinner text-white"></span>
    </div>
    <div
      v-else-if="!posts.length || error"
      class="flex h-full items-center justify-center px-6 text-center text-white/70"
    >
      {{ error || emptyText }}
    </div>
    <div ref="sentinel" class="h-px"></div>
  </div>
</template>

<script>
import PostCard from '@/components/posts/PostCard.vue'
import { apiFetch } from '@/lib/api.js'

export default {
  name: 'ReelFeed',
  components: { PostCard },
  props: {
    url: { type: String, default: null },
    initialPosts: { type: Array, default: () => [] },
    emptyText: { type: String, default: 'Noch keine Reels.' },
  },
  emits: ['deleted'],
  data() {
    return {
      posts: [...this.initialPosts],
      nextQuery: null,
      hasMore: Boolean(this.url),
      loading: false,
      error: null,
    }
  },
  mounted() {
    this.observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) this.loadMore()
      },
      { root: this.$refs.scroller, rootMargin: '0px 0px 200% 0px' },
    )
    this.observer.observe(this.$refs.sentinel)
  },
  beforeUnmount() {
    this.observer.disconnect()
  },
  methods: {
    async loadMore() {
      if (this.loading || !this.hasMore || this.error) return
      this.loading = true
      try {
        const url = new URL(this.url, window.location.origin)
        for (const [key, value] of this.nextQuery ?? []) url.searchParams.set(key, value)
        const response = await apiFetch(url.pathname + url.search)
        if (!response.ok) {
          this.error = 'Reels konnten nicht geladen werden.'
          return
        }
        const data = await response.json()
        this.posts.push(...data.results)
        this.nextQuery = data.next && new URL(data.next, window.location.origin).searchParams
        this.hasMore = Boolean(this.nextQuery)
      } finally {
        this.loading = false
      }
      await this.$nextTick()
      this.observer.unobserve(this.$refs.sentinel)
      this.observer.observe(this.$refs.sentinel)
    },
    remove(id) {
      this.posts = this.posts.filter((post) => post.id !== id)
      this.$emit('deleted', id)
    },
  },
}
</script>

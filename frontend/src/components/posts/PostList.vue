<template>
  <div>
    <div v-if="grid && posts.length" class="grid grid-cols-3 gap-1 max-sm:-mx-6">
      <PostTile v-for="post in posts" :key="post.id" :post="post" :reel-base="reelBase" />
    </div>

    <div
      v-else-if="posts.length"
      class="flex flex-col gap-4"
      :class="{ 'max-sm:gap-2 max-sm:bg-base-200': edgeToEdge }"
    >
      <template v-for="item in posts" :key="itemKey(item)">
        <CommentActivity
          v-if="item.type === 'comment'"
          :comment="item"
          :edge-to-edge="edgeToEdge"
        />
        <PostCard
          v-else
          :post="item"
          :folder-picker="folderPicker"
          :edge-to-edge="edgeToEdge"
          @deleted="remove"
          @saved-change="(change) => $emit('saved-change', item, change)"
        />
      </template>
    </div>

    <BaseCard v-else-if="!hasMore && !loading" class="p-6">
      <p class="text-swissfy-muted">{{ emptyText }}</p>
    </BaseCard>

    <p v-if="error" class="text-error text-sm mt-4 text-center">{{ error }}</p>

    <div v-if="loading" :class="grid ? 'grid grid-cols-3 gap-1 mt-1' : 'flex flex-col gap-4 mt-4'">
      <div v-for="n in 3" :key="n" class="skeleton" :class="grid ? 'aspect-square' : 'h-48'"></div>
    </div>

    <div ref="sentinel" class="h-px"></div>
  </div>
</template>

<script>
import BaseCard from '@/components/common/BaseCard.vue'
import CommentActivity from '@/components/posts/CommentActivity.vue'
import PostCard from '@/components/posts/PostCard.vue'
import PostTile from '@/components/posts/PostTile.vue'
import api from '@/api/client.js'

function itemKey(item) {
  return `${item.type ?? 'post'}-${item.id}`
}

export default {
  name: 'PostList',
  components: { BaseCard, CommentActivity, PostCard, PostTile },
  props: {
    url: { type: String, required: true },
    grid: { type: Boolean, default: false },
    folderPicker: { type: Boolean, default: false },
    edgeToEdge: { type: Boolean, default: false },
    emptyText: { type: String, default: 'Noch keine Feeds.' },
    reelBase: { type: String, default: null },
  },
  emits: ['saved-change'],
  data() {
    return {
      posts: [],
      nextQuery: null,
      hasMore: true,
      loading: false,
      error: null,
    }
  },
  mounted() {
    this.observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting) this.loadMore()
    })
    this.observer.observe(this.$refs.sentinel)
  },
  beforeUnmount() {
    this.observer.disconnect()
  },
  methods: {
    itemKey,
    async loadMore() {
      if (this.loading || !this.hasMore || this.error) return
      this.loading = true
      try {
        const url = new URL(this.url, window.location.origin)
        for (const [key, value] of this.nextQuery ?? []) url.searchParams.set(key, value)
        const data = await api.get(url.pathname + url.search)
        const known = new Set(this.posts.map(itemKey))
        this.posts.push(...data.results.filter((item) => !known.has(itemKey(item))))
        this.nextQuery = data.next && new URL(data.next, window.location.origin).searchParams
        this.hasMore = Boolean(this.nextQuery)
      } catch {
        this.error = 'Feeds konnten nicht geladen werden.'
      } finally {
        this.loading = false
      }
      await this.$nextTick()
      this.observer.unobserve(this.$refs.sentinel)
      this.observer.observe(this.$refs.sentinel)
    },
    remove(id) {
      this.posts = this.posts.filter((item) => item.type === 'comment' || item.id !== id)
    },
  },
}
</script>

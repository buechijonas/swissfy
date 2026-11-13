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
      <template v-for="item in posts" :key="postKey(item)">
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
          @update="replace"
          @deleted="remove"
          @saved-change="(change) => $emit('saved-change', item, change)"
        />
      </template>
    </div>

    <BaseCard v-else-if="!hasMore && !loading" class="p-6">
      <p class="text-app-muted">{{ emptyText }}</p>
    </BaseCard>

    <ErrorText :message="error" class="mt-4 text-center" />

    <div v-if="loading" :class="grid ? 'grid grid-cols-3 gap-1 mt-1' : 'flex flex-col gap-4 mt-4'">
      <div v-for="n in 3" :key="n" class="skeleton" :class="grid ? 'aspect-square' : 'h-48'"></div>
    </div>

    <div v-intersect="onSentinel" class="h-px"></div>
  </div>
</template>

<script>
import ErrorText from '@core/components/ErrorText.vue'
import map from 'lodash-es/map'
import reject from 'lodash-es/reject'
import BaseCard from '@core/components/BaseCard.vue'
import CommentActivity from '@/components/posts/CommentActivity.vue'
import PostCard from '@/components/posts/PostCard.vue'
import PostTile from '@/components/posts/PostTile.vue'
import intersect from '@/directives/intersect.js'
import postFeedMixin from '@/mixins/postFeedMixin.js'

export default {
  name: 'PostList',
  components: { BaseCard, CommentActivity, PostCard, PostTile, ErrorText },
  directives: { intersect },
  mixins: [postFeedMixin],
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
    return { loadError: 'Feeds konnten nicht geladen werden.' }
  },
  methods: {
    postKey(item) {
      return `${item.type ?? 'post'}-${item.id}`
    },
    appendPosts(posts) {
      const known = new Set(map(this.posts, this.postKey))
      this.posts.push(...reject(posts, (item) => known.has(this.postKey(item))))
    },
    remove(id) {
      this.posts = reject(this.posts, (item) => item.type !== 'comment' && item.id === id)
    },
  },
}
</script>

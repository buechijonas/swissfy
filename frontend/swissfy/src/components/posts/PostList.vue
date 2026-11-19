<template>
  <div>
    <div v-if="grid && feed.posts.length" class="grid grid-cols-3 gap-1 max-sm:-mx-6">
      <PostTile v-for="post in feed.posts" :key="post.id" :post="post" :reel-base="reelBase" />
    </div>

    <div
      v-else-if="feed.posts.length"
      class="flex flex-col gap-4"
      :class="{ 'max-sm:gap-2 max-sm:bg-base-200': edgeToEdge }"
    >
      <template v-for="item in feed.posts" :key="feed.key(item)">
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
          @update="feed.replace"
          @deleted="remove"
          @saved-change="(change) => $emit('saved-change', item, change)"
        />
      </template>
    </div>

    <BaseCard v-else-if="!feed.hasMore && !feed.loading" class="p-6">
      <p class="text-app-muted">{{ emptyTextOrDefault }}</p>
    </BaseCard>

    <ErrorText :message="feed.error" class="mt-4 text-center" />

    <div
      v-if="feed.loading"
      :class="grid ? 'mt-1 grid grid-cols-3 gap-1' : 'mt-4 flex flex-col gap-4'"
    >
      <div v-for="n in 3" :key="n" class="skeleton" :class="grid ? 'aspect-square' : 'h-48'"></div>
    </div>

    <div v-intersect="feed.onSentinel" class="h-px"></div>
  </div>
</template>

<script>
import BaseCard from '@core/components/BaseCard.vue'
import ErrorText from '@core/components/ErrorText.vue'
import CommentActivity from '@/components/posts/CommentActivity.vue'
import PostCard from '@/components/posts/PostCard.vue'
import PostTile from '@/components/posts/PostTile.vue'
import { usePostFeed } from '@/composables/postFeed.js'
import intersect from '@/directives/intersect.js'
import { t } from '@/i18n.js'

function itemKey(item) {
  return `${item.type ?? 'post'}-${item.id}`
}

export default {
  name: 'PostList',
  components: { BaseCard, CommentActivity, PostCard, PostTile, ErrorText },
  directives: { intersect },
  props: {
    url: { type: String, required: true },
    grid: { type: Boolean, default: false },
    folderPicker: { type: Boolean, default: false },
    edgeToEdge: { type: Boolean, default: false },
    emptyText: { type: String, default: null },
    reelBase: { type: String, default: null },
  },
  emits: ['saved-change'],
  data() {
    return {
      feed: usePostFeed({
        url: () => this.url,
        loadError: () => t('postList.loadFailed'),
        key: itemKey,
      }),
    }
  },
  computed: {
    emptyTextOrDefault() {
      return this.emptyText ?? t('postList.empty')
    },
  },
  methods: {
    remove(id) {
      this.feed.remove((item) => item.type !== 'comment' && item.id === id)
    },
  },
}
</script>

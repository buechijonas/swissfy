<template>
  <footer
    class="flex"
    :class="
      reel
        ? 'absolute right-3 bottom-28 flex-col items-center gap-5 text-white drop-shadow'
        : 'items-start gap-6 px-4 py-3'
    "
  >
    <PostAction
      :icon="post.liked ? 'heart-filled' : 'heart'"
      title="Gefällt mir"
      :label="post.like_count"
      :disabled="busy"
      :icon-class="{ 'text-primary': post.liked }"
      @select="$emit('like')"
    />
    <PostAction
      icon="comment-alt-middle"
      title="Kommentare"
      :label="post.comment_count"
      :interactive="commentable"
      @select="$emit('comments')"
    />
    <PostAction
      icon="arrows-retweet"
      :title="post.reposted ? 'Repost entfernen' : 'Reposten'"
      :label="repostLabel"
      :disabled="busy || post.is_own"
      :icon-class="{ 'text-swissfy-repost': post.reposted, 'opacity-40': post.is_own }"
      label-class="max-w-20 truncate"
      @select="$emit('repost')"
    />
    <PostAction
      :class="{ 'ml-auto': !reel }"
      :icon="post.saved ? 'bookmarked' : 'bookmark'"
      :title="post.saved ? 'Nicht mehr speichern' : 'Speichern'"
      :label="reel ? null : formatRelativeTime(post.created_at)"
      :disabled="busy"
      :align="reel ? 'center' : 'end'"
      label-class="text-swissfy-muted"
      @select="$emit('save')"
    />
    <PostAction
      v-if="reel && hasMenu"
      icon="menu-dots-vertical"
      title="Mehr"
      @select="$emit('menu')"
    />
  </footer>
</template>

<script>
import PostAction from '@/components/posts/PostAction.vue'
import { formatRelativeTime } from '@/lib/time.js'

export default {
  name: 'PostActions',
  components: { PostAction },
  props: {
    post: { type: Object, required: true },
    reel: { type: Boolean, default: false },
    busy: { type: Boolean, default: false },
    commentable: { type: Boolean, default: false },
    hasMenu: { type: Boolean, default: false },
  },
  emits: ['like', 'comments', 'repost', 'save', 'menu'],
  computed: {
    repostLabel() {
      if (this.post.reposter) return `@${this.post.reposter}`
      return this.post.reposted ? 'Du' : ''
    },
  },
  methods: {
    formatRelativeTime,
  },
}
</script>

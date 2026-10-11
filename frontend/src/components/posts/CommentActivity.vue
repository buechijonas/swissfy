<template>
  <BaseCard tag="article" :inset="!edgeToEdge" :class="{ 'max-sm:border-y-0': edgeToEdge }">
    <AuthorHeader :author="comment.author" />
    <div class="flex flex-col gap-3 px-4 py-3">
      <p class="text-xs text-swissfy-muted">
        {{ comment.reply_to ? `Antwort an @${comment.reply_to}` : 'Kommentar' }} ·
        {{ formatRelativeTime(comment.created_at) }}
      </p>
      <RouterLink :to="commentLink(comment)" class="whitespace-pre-line break-words">
        {{ comment.text }}
      </RouterLink>
      <RouterLink
        :to="`/posts/${post.id}`"
        class="flex items-center gap-3 rounded-box border border-swissfy-border p-3 hover:bg-base-200"
      >
        <img
          v-if="post.thumbnail"
          class="size-14 shrink-0 object-cover"
          :src="post.thumbnail"
          alt=""
          loading="lazy"
        />
        <div class="flex min-w-0 flex-col">
          <span class="flex min-w-0 items-center gap-1">
            <span class="text-sm font-bold truncate">@{{ post.author.username }}</span>
            <RoleBadge :role="post.author.role" />
          </span>
          <p v-if="post.text" class="text-sm text-swissfy-muted line-clamp-2 break-words">
            {{ post.text }}
          </p>
        </div>
      </RouterLink>
    </div>
  </BaseCard>
</template>

<script>
import { RouterLink } from 'vue-router'
import BaseCard from '@/components/common/BaseCard.vue'
import RoleBadge from '@/components/common/RoleBadge.vue'
import AuthorHeader from '@/components/posts/AuthorHeader.vue'
import { commentLink } from '@/lib/comments.js'
import { formatRelativeTime } from '@/lib/time.js'

export default {
  name: 'CommentActivity',
  components: { RouterLink, AuthorHeader, BaseCard, RoleBadge },
  props: {
    comment: { type: Object, required: true },
    edgeToEdge: { type: Boolean, default: false },
  },
  computed: {
    post() {
      return this.comment.post
    },
  },
  methods: {
    commentLink,
    formatRelativeTime,
  },
}
</script>

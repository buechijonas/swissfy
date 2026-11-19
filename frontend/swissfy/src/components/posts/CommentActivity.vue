<template>
  <BaseCard tag="article" :inset="!edgeToEdge" :class="{ 'max-sm:border-y-0': edgeToEdge }">
    <AuthorHeader :author="comment.author" />
    <div class="flex flex-col gap-3 px-4 py-3">
      <p class="text-xs text-app-muted">
        {{
          comment.reply_to
            ? $t('comments.replyToUser', { username: comment.reply_to })
            : $t('comments.comment')
        }}
        ·
        {{ formatRelativeTime(comment.created_at) }}
      </p>
      <RouterLink :to="commentLink(comment)" class="break-words whitespace-pre-line">
        {{ comment.text }}
      </RouterLink>
      <RouterLink
        :to="`/posts/${post.id}`"
        class="flex items-center gap-3 rounded-box border border-app-border p-3 hover:bg-base-200"
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
            <span class="truncate text-sm font-bold">@{{ post.author.username }}</span>
            <RoleBadge :role="post.author.role" />
          </span>
          <p v-if="post.text" class="line-clamp-2 text-sm break-words text-app-muted">
            {{ post.text }}
          </p>
        </div>
      </RouterLink>
    </div>
  </BaseCard>
</template>

<script>
import { RouterLink } from 'vue-router'
import BaseCard from '@core/components/BaseCard.vue'
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

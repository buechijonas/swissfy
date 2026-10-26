<template>
  <div
    class="relative flex gap-3 pr-4 py-3"
    :class="[PADDING[depth], { 'cursor-pointer hover:bg-base-200/50': !focused }]"
    @click="open"
  >
    <template v-if="depth > 0">
      <span
        class="absolute top-0 h-7 w-6 -translate-x-px rounded-bl-lg border-b-2 border-l-2 border-swissfy-border"
        :class="CENTER[depth - 1]"
      ></span>
      <span
        v-if="siblingBelow"
        class="absolute top-0 bottom-0 w-0.5 -translate-x-1/2 bg-swissfy-border"
        :class="CENTER[depth - 1]"
      ></span>
    </template>
    <span
      v-else-if="lineAbove"
      class="absolute top-0 h-2 w-0.5 -translate-x-1/2 bg-swissfy-border"
      :class="CENTER[depth]"
    ></span>
    <span
      v-if="lineBelow"
      class="absolute top-12 bottom-0 w-0.5 -translate-x-1/2 bg-swissfy-border"
      :class="CENTER[depth]"
    ></span>

    <RouterLink :to="profileLink(comment.author)" class="shrink-0">
      <UserAvatar class="size-8" :user="comment.author" />
    </RouterLink>
    <div class="flex min-w-0 flex-1 flex-col">
      <div class="flex flex-wrap items-center gap-x-2">
        <RouterLink :to="profileLink(comment.author)" class="font-bold truncate max-w-full">
          {{ comment.author.username }}
        </RouterLink>
        <RoleBadge :role="comment.author.role" />
        <span v-if="comment.is_post_author" class="text-xs font-bold text-error shrink-0">
          Verfasser
        </span>
        <span class="text-xs text-swissfy-muted shrink-0">
          {{ formatRelativeTime(comment.created_at) }}
        </span>
        <span v-if="comment.hidden" class="text-xs font-bold text-error shrink-0">Verborgen</span>
      </div>
      <p v-if="showReplyTo && comment.reply_to" class="text-xs text-swissfy-muted">
        Antwort an
        <RouterLink :to="profileLink({ username: comment.reply_to })" class="link">
          @{{ comment.reply_to }}
        </RouterLink>
      </p>
      <p
        v-if="comment.text"
        class="whitespace-pre-line break-words"
        :class="{ 'text-lg mt-1': focused }"
      >
        {{ comment.text }}
      </p>
      <img
        v-if="comment.thumbnail"
        class="mt-2 size-20 object-cover bg-base-200"
        :src="comment.thumbnail"
        alt=""
        loading="lazy"
      />
      <div class="mt-1 flex flex-wrap items-center gap-2">
        <span class="flex items-center gap-1 text-xs text-swissfy-muted">
          <AppIcon name="comment-alt-middle" size="sm" alt="Antworten" />
          {{ count ?? comment.reply_count }}
        </span>
        <div v-if="'score' in comment" class="ml-auto flex items-center gap-2">
          <span
            class="min-w-5 text-right text-sm leading-none"
            :class="myVote ? 'text-primary' : 'text-swissfy-muted'"
          >
            {{ score }}
          </span>
          <DeleteButton v-if="comment.can_delete" @click="$emit('delete', comment)" />
          <template v-else-if="comment.can_vote">
            <BaseButton
              v-for="option in voteOptions"
              :key="option.value"
              :variant="myVote === option.value ? 'primary' : 'neutral'"
              :outline="myVote !== option.value"
              shape="square"
              size="sm"
              :disabled="voting"
              :title="option.label"
              @click="vote(option.value)"
            >
              <AppIcon :name="option.icon" :alt="option.label" />
            </BaseButton>
          </template>
          <BaseButton
            v-if="comment.can_report"
            outline
            size="sm"
            :disabled="reporting || reported"
            @click="report"
          >
            <AppIcon name="flag" />
            {{ reported ? 'Gemeldet' : 'Melden' }}
          </BaseButton>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { RouterLink } from 'vue-router'
import AppIcon from '@/components/common/AppIcon.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import DeleteButton from '@/components/common/DeleteButton.vue'
import RoleBadge from '@/components/common/RoleBadge.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import commentsApi from '@/api/comments.js'
import { commentLink } from '@/lib/comments.js'
import { formatRelativeTime } from '@/lib/time.js'

const PADDING = ['pl-4', 'pl-15', 'pl-26']
const CENTER = ['left-8', 'left-19', 'left-30']

export default {
  name: 'CommentItem',
  components: { RouterLink, AppIcon, BaseButton, DeleteButton, RoleBadge, UserAvatar },
  props: {
    comment: { type: Object, required: true },
    depth: { type: Number, default: 0 },
    to: { type: String, default: null },
    count: { type: Number, default: null },
    siblingBelow: { type: Boolean, default: false },
    lineAbove: { type: Boolean, default: false },
    lineBelow: { type: Boolean, default: false },
    focused: { type: Boolean, default: false },
    showReplyTo: { type: Boolean, default: false },
    moderation: { type: Boolean, default: false },
  },
  emits: ['delete'],
  data() {
    return {
      PADDING,
      CENTER,
      score: this.comment.score,
      myVote: this.comment.my_vote,
      voting: false,
      reported: this.comment.reported,
      reporting: false,
      voteOptions: [
        { value: 1, icon: 'arrow-up', label: 'Upvote' },
        { value: -1, icon: 'arrow-down', label: 'Downvote' },
      ],
    }
  },
  watch: {
    comment(comment) {
      this.score = comment.score
      this.myVote = comment.my_vote
      this.reported = comment.reported
    },
  },
  methods: {
    formatRelativeTime,
    profileLink(author) {
      return `/profile/${encodeURIComponent(author.username)}`
    },
    async vote(value) {
      this.voting = true
      try {
        const data = await commentsApi
          .vote(this.comment.id, this.myVote === value ? 0 : value)
          .catch(() => null)
        if (!data) return
        this.score = data.score
        this.myVote = data.my_vote
      } finally {
        this.voting = false
      }
    },
    async report() {
      this.reporting = true
      try {
        await commentsApi.report(this.comment.id)
        this.reported = true
      } catch {
        this.reported = false
      } finally {
        this.reporting = false
      }
    },
    open(event) {
      if (this.focused || event.target.closest('a, button')) return
      this.$router.push(this.to ?? commentLink(this.comment, this.moderation))
    },
  },
}
</script>

<template>
  <div>
    <template v-if="!nested">
      <slot name="composer">
        <CommentForm v-model="draft" :placeholder="placeholder" :sending="sending" @submit="add" />
      </slot>
      <p v-if="error" class="text-error text-sm mt-2">{{ error }}</p>
    </template>
    <BaseCard v-if="comments.length || $slots.head" :class="{ 'mt-4': !nested }">
      <slot name="head" />
      <div v-if="nested" class="relative pl-15 pr-4 py-3">
        <span
          v-if="comments.length"
          class="absolute left-8 top-0 bottom-0 w-0.5 -translate-x-1/2 bg-swissfy-border"
        ></span>
        <slot name="composer">
          <CommentForm
            v-model="draft"
            :placeholder="placeholder"
            :sending="sending"
            @submit="add"
          />
        </slot>
        <p v-if="error" class="text-error text-sm mt-2">{{ error }}</p>
      </div>
      <ul v-if="nested">
        <li v-for="(comment, index) in comments" :key="comment.id">
          <CommentItem
            :comment="comment"
            :depth="1"
            :sibling-below="index < comments.length - 1"
            :moderation="moderation"
            @delete="confirmRemove"
          />
        </li>
      </ul>
      <ul v-else class="divide-y divide-swissfy-border">
        <li v-for="comment in comments" :key="comment.id">
          <CommentItem
            :comment="comment"
            :line-below="!!comment.latest_reply"
            :moderation="moderation"
            @delete="confirmRemove"
          />
          <template v-if="comment.latest_reply">
            <CommentItem
              :comment="comment.latest_reply"
              :depth="1"
              :moderation="moderation"
              @delete="confirmRemove"
            />
            <RouterLink
              v-if="comment.reply_count > 1"
              :to="commentLink(comment, moderation)"
              class="block pl-15 pb-3 text-sm text-swissfy-muted link"
            >
              Alle {{ comment.reply_count }} Antworten anzeigen
            </RouterLink>
          </template>
        </li>
      </ul>
    </BaseCard>
    <BaseButton v-if="cursor" class="mt-2" size="sm" block @click="load">
      <AppIcon name="down" />
      Weitere Kommentare laden
    </BaseButton>

    <ConfirmDialog
      ref="confirm"
      message="Willst du diesen Kommentar löschen? Antworten darauf werden auch gelöscht."
      @confirm="remove(pending)"
    />
  </div>
</template>

<script>
import { RouterLink } from 'vue-router'
import AppIcon from '@/components/common/AppIcon.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import CommentForm from '@/components/posts/CommentForm.vue'
import CommentItem from '@/components/posts/CommentItem.vue'
import { apiFetch, extractErrorMessage } from '@/lib/api.js'
import { commentLink } from '@/lib/comments.js'

export default {
  name: 'CommentSection',
  components: {
    RouterLink,
    AppIcon,
    BaseButton,
    BaseCard,
    ConfirmDialog,
    CommentForm,
    CommentItem,
  },
  props: {
    url: { type: String, required: true },
    placeholder: { type: String, default: 'Kommentar schreiben…' },
    nested: { type: Boolean, default: false },
    moderation: { type: Boolean, default: false },
  },
  emits: ['created', 'deleted'],
  data() {
    return {
      comments: [],
      cursor: null,
      draft: '',
      sending: false,
      error: null,
      pending: null,
    }
  },
  created() {
    this.load()
  },
  methods: {
    commentLink,
    async load() {
      const query = this.cursor ? `?cursor=${encodeURIComponent(this.cursor)}` : ''
      const response = await apiFetch(`${this.url}${query}`)
      if (!response.ok) return
      const data = await response.json()
      const known = new Set(this.comments.map((comment) => comment.id))
      this.comments.push(...data.results.filter((comment) => !known.has(comment.id)))
      this.cursor = data.next && new URL(data.next).searchParams.get('cursor')
    },
    async add() {
      this.sending = true
      this.error = null
      try {
        const response = await apiFetch(this.url, {
          method: 'POST',
          body: JSON.stringify({ text: this.draft.trim() }),
        })
        const data = await response.json().catch(() => null)
        if (!response.ok) {
          this.error = extractErrorMessage(data, 'Kommentar konnte nicht gesendet werden.')
          return
        }
        this.comments.unshift(data)
        this.$emit('created', data)
        this.draft = ''
      } finally {
        this.sending = false
      }
    },
    confirmRemove(comment) {
      this.pending = comment
      this.$refs.confirm.open()
    },
    async remove(comment) {
      const response = await apiFetch(`/api/comments/${comment.id}/`, { method: 'DELETE' })
      if (!response.ok) {
        this.error = 'Kommentar konnte nicht gelöscht werden.'
        return
      }
      const data = await response.json()
      this.comments = this.comments
        .filter((item) => item.id !== comment.id)
        .map((item) => (item.id === data.parent?.id ? data.parent : item))
      this.$emit('deleted', data)
    },
  },
}
</script>

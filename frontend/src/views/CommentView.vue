<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div
    class="flex flex-col pb-8 px-6 max-h-[calc(100dvh-96px)] overflow-y-auto lg:max-h-none lg:overflow-y-visible lg:flex-1"
  >
    <div class="mx-auto w-full max-w-150 sm:pt-4">
      <BaseCard v-if="error" class="p-6">
        <p class="text-swissfy-muted">{{ error }}</p>
      </BaseCard>
      <div v-else-if="!comment" class="skeleton h-96 w-full"></div>
      <template v-else>
        <CommentSection
          :key="repliesUrl"
          :url="repliesUrl"
          nested
          placeholder="Antwort schreiben…"
          @created="comment.reply_count += 1"
          @deleted="comment.reply_count = $event.parent.reply_count"
        >
          <template #head>
            <CommentItem
              :comment="comment.post"
              :to="postLink"
              :count="comment.post.comment_count"
              line-below
            />
            <CommentItem
              v-for="ancestor in comment.ancestors"
              :key="ancestor.id"
              :comment="ancestor"
              line-above
              line-below
              show-reply-to
              @delete="confirmRemove"
            />
            <CommentItem
              :comment="comment"
              line-above
              :line-below="comment.reply_count > 0"
              focused
              show-reply-to
              @delete="confirmRemove"
            />
          </template>
        </CommentSection>
        <p v-if="deleteError" class="text-error text-sm mt-2">{{ deleteError }}</p>
        <ConfirmDialog
          ref="confirm"
          message="Willst du diesen Kommentar löschen? Antworten darauf werden auch gelöscht."
          @confirm="remove(pending)"
        />
      </template>
    </div>
  </div>
  <BaseFooter />
</template>

<script>
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import CommentItem from '@/components/posts/CommentItem.vue'
import CommentSection from '@/components/posts/CommentSection.vue'
import { apiFetch } from '@/lib/api.js'
import { commentLink } from '@/lib/comments.js'

export default {
  name: 'CommentView',
  components: {
    BaseBreadcrumbs,
    BaseCard,
    BaseFooter,
    ConfirmDialog,
    CommentItem,
    CommentSection,
  },
  data() {
    return {
      comment: null,
      error: null,
      deleteError: null,
      pending: null,
    }
  },
  computed: {
    apiBase() {
      return `/api/comments/${this.$route.params.id}`
    },
    repliesUrl() {
      return `${this.apiBase}/replies/`
    },
    postLink() {
      return this.comment && `/posts/${this.comment.post.id}`
    },
    breadcrumbs() {
      return [
        ...(this.postLink ? [{ label: 'Post', to: this.postLink }] : []),
        { label: 'Kommentar', to: this.$route.path },
      ]
    },
  },
  watch: {
    '$route.params.id'(id) {
      if (id) this.load()
    },
  },
  created() {
    this.load()
  },
  methods: {
    async load() {
      this.error = null
      this.comment = null
      try {
        const response = await apiFetch(`${this.apiBase}/`)
        if (!response.ok) {
          this.error =
            response.status === 404
              ? 'Kommentar nicht gefunden.'
              : 'Kommentar konnte nicht geladen werden.'
          return
        }
        this.comment = await response.json()
      } catch {
        this.error = 'Kommentar konnte nicht geladen werden.'
      }
    },
    confirmRemove(comment) {
      this.pending = comment
      this.$refs.confirm.open()
    },
    async remove(comment) {
      this.deleteError = null
      const response = await apiFetch(`/api/comments/${comment.id}/`, { method: 'DELETE' })
      if (!response.ok) {
        this.deleteError = 'Kommentar konnte nicht gelöscht werden.'
        return
      }
      const { parent } = await response.json()
      this.$router.replace(parent ? commentLink(parent) : this.postLink)
    },
  },
}
</script>

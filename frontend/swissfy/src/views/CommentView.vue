<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div
    class="flex flex-col pb-8 px-6 max-h-[calc(100dvh-var(--mobile-chrome-height))] overflow-y-auto lg:max-h-none lg:overflow-y-visible lg:flex-1"
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
          :moderation="moderation"
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
              :moderation="moderation"
              @delete="confirmRemove"
            />
            <CommentItem
              :comment="comment"
              line-above
              :line-below="comment.reply_count > 0"
              focused
              show-reply-to
              :moderation="moderation"
              @delete="confirmRemove"
            />
          </template>
          <template v-if="moderation" #composer>
            <ModerationPanel
              :key="comment.id"
              kind="comments"
              :target-id="comment.id"
              :details="comment"
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
import ModerationPanel from '@/components/moderation/ModerationPanel.vue'
import CommentItem from '@/components/posts/CommentItem.vue'
import CommentSection from '@/components/posts/CommentSection.vue'
import commentsApi from '@/api/comments.js'
import moderationApi from '@/api/moderation.js'
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
    ModerationPanel,
  },
  props: {
    moderation: { type: Boolean, default: false },
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
    id() {
      return this.$route.params.id
    },
    repliesUrl() {
      return this.moderation
        ? moderationApi.childrenUrl('comments', this.id)
        : commentsApi.repliesUrl(this.id)
    },
    postLink() {
      if (!this.comment) return null
      const base = this.moderation ? '/moderation/posts' : '/posts'
      return `${base}/${this.comment.post.id}`
    },
    breadcrumbs() {
      return [
        ...(this.moderation ? [{ label: 'Moderation', to: '/moderation' }] : []),
        ...(this.postLink ? [{ label: 'Feed', to: this.postLink }] : []),
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
        this.comment = this.moderation
          ? await moderationApi.get('comments', this.id)
          : await commentsApi.get(this.id)
      } catch (error) {
        this.error =
          error.status === 404
            ? 'Kommentar nicht gefunden.'
            : 'Kommentar konnte nicht geladen werden.'
      }
    },
    confirmRemove(comment) {
      this.pending = comment
      this.$refs.confirm.open()
    },
    async remove(comment) {
      this.deleteError = null
      const data = await commentsApi.remove(comment.id).catch(() => null)
      if (!data) {
        this.deleteError = 'Kommentar konnte nicht gelöscht werden.'
        return
      }
      const { parent } = data
      this.$router.replace(parent ? commentLink(parent) : this.postLink)
    },
  },
}
</script>

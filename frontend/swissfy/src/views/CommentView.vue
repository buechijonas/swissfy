<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div
    class="flex max-h-[calc(100dvh-var(--mobile-chrome-height))] flex-col overflow-y-auto px-6 pb-8 lg:max-h-none lg:flex-1 lg:overflow-y-visible"
  >
    <div class="mx-auto w-full max-w-150 sm:pt-4">
      <BaseCard v-if="error" class="p-6">
        <p class="text-app-muted">{{ error }}</p>
      </BaseCard>
      <div v-else-if="!comment" class="h-96 w-full skeleton"></div>
      <template v-else>
        <CommentSection
          :key="repliesUrl"
          :url="repliesUrl"
          nested
          :moderation="moderation"
          :placeholder="$t('commentView.replyPlaceholder')"
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
        <ErrorText :message="deleteError" class="mt-2" />
        <ConfirmDialog
          ref="confirm"
          :message="$t('commentView.deleteMessage')"
          @confirm="remove(pending)"
        />
      </template>
    </div>
  </div>
  <BaseFooter />
</template>

<script>
import BaseCard from '@core/components/BaseCard.vue'
import ErrorText from '@core/components/ErrorText.vue'
import commentsApi from '@/api/comments.js'
import moderationApi from '@/api/moderation.js'
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import ModerationPanel from '@/components/moderation/ModerationPanel.vue'
import CommentItem from '@/components/posts/CommentItem.vue'
import CommentSection from '@/components/posts/CommentSection.vue'
import { t } from '@/i18n.js'
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
    ErrorText,
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
        ...(this.moderation ? [{ label: t('commentView.moderation'), to: '/moderation' }] : []),
        ...(this.postLink ? [{ label: t('commentView.post'), to: this.postLink }] : []),
        { label: t('commentView.comment'), to: this.$route.path },
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
        this.error = error.status === 404 ? t('commentView.notFound') : t('commentView.loadFailed')
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
        this.deleteError = t('commentView.deleteFailed')
        return
      }
      const { parent } = data
      this.$router.replace(parent ? commentLink(parent) : this.postLink)
    },
  },
}
</script>

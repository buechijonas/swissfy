<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div
    class="flex max-h-[calc(100dvh-var(--mobile-chrome-height))] flex-col overflow-y-auto px-6 pb-8 max-sm:pb-0 lg:max-h-none lg:flex-1 lg:overflow-y-visible"
  >
    <div class="mx-auto w-full max-w-150 pt-4">
      <BaseTabs class="mb-4" :tabs="tabs" :active="status" />
      <div v-if="items.length" class="flex flex-col gap-6">
        <section v-for="item in items" :key="`${item.type}-${itemId(item)}`">
          <p class="mb-2 text-sm" :class="resolved ? 'text-app-muted' : 'text-error'">
            {{ caption(item) }}
          </p>
          <PostCard
            v-if="item.type === 'post'"
            :post="item.post"
            moderation
            @update="item.post = $event"
          />
          <BaseCard v-else>
            <CommentItem
              :comment="item.post"
              :to="`/moderation/posts/${item.post.id}`"
              :count="item.post.comment_count"
              line-below
            />
            <CommentItem :comment="item.comment" line-above show-reply-to moderation />
          </BaseCard>
        </section>
      </div>
      <BaseCard v-else-if="!loading && !error" class="p-6">
        <p class="text-app-muted">
          {{ resolved ? $t('moderation.noResolved') : $t('moderation.noOpen') }}
        </p>
      </BaseCard>

      <ErrorText :message="error" class="mt-4 text-center" />
      <div v-if="loading" class="mt-4 h-48 w-full skeleton"></div>
      <BaseButton v-else-if="next" class="mt-4" size="sm" block @click="load">
        <AppIcon name="down" />
        {{ $t('common.loadMore') }}
      </BaseButton>
    </div>
  </div>
  <BaseFooter />
</template>

<script>
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import BaseCard from '@core/components/BaseCard.vue'
import ErrorText from '@core/components/ErrorText.vue'
import moderationApi from '@/api/moderation.js'
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import BaseTabs from '@/components/common/BaseTabs.vue'
import CommentItem from '@/components/posts/CommentItem.vue'
import PostCard from '@/components/posts/PostCard.vue'
import { t } from '@/i18n.js'

export default {
  name: 'ModerationView',
  components: {
    AppIcon,
    BaseBreadcrumbs,
    BaseButton,
    BaseCard,
    BaseFooter,
    BaseTabs,
    CommentItem,
    PostCard,
    ErrorText,
  },
  data() {
    return {
      items: [],
      next: null,
      loading: false,
      error: null,
    }
  },
  computed: {
    tabs() {
      return [
        { key: 'open', label: t('moderation.open') },
        { key: 'resolved', label: t('moderation.resolved') },
      ]
    },
    breadcrumbs() {
      return [{ label: t('moderation.title'), to: '/moderation' }]
    },
    status() {
      return this.$route.query.tab === 'resolved' ? 'resolved' : 'open'
    },
    resolved() {
      return this.status === 'resolved'
    },
  },
  watch: {
    status() {
      this.reload()
    },
  },
  created() {
    this.reload()
  },
  methods: {
    caption(item) {
      const parts = [
        item.type === 'post' ? t('moderation.post') : t('moderation.comment'),
        `${item.report_count}× gemeldet`,
      ]
      if (this.resolved) parts.push(item.warned ? 'verwarnt' : 'verworfen')
      return parts.join(' · ')
    },
    reload() {
      this.items = []
      this.next = moderationApi.reportsUrl(this.status)
      this.load()
    },
    itemId(item) {
      return item.type === 'post' ? item.post.id : item.comment.id
    },
    async load() {
      const url = this.next
      this.loading = true
      this.error = null
      try {
        const data = await moderationApi.list(url)
        if (url !== this.next) return
        this.items.push(...data.results)
        this.next = data.next
      } catch {
        this.error = t('moderation.loadFailed')
      } finally {
        this.loading = false
      }
    },
  },
}
</script>

<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div
    class="flex flex-col pb-8 px-6 max-sm:pb-0 max-h-[calc(100dvh-var(--mobile-chrome-height))] overflow-y-auto lg:max-h-none lg:overflow-y-visible lg:flex-1"
  >
    <div class="mx-auto w-full max-w-150 pt-4">
      <BaseTabs class="mb-4" :tabs="tabs" :active="status" />
      <div v-if="items.length" class="flex flex-col gap-6">
        <section v-for="item in items" :key="`${item.type}-${itemId(item)}`">
          <p class="mb-2 text-sm" :class="resolved ? 'text-swissfy-muted' : 'text-error'">
            {{ caption(item) }}
          </p>
          <PostCard v-if="item.type === 'post'" :post="item.post" moderation />
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
        <p class="text-swissfy-muted">
          {{ resolved ? 'Noch keine erledigten Meldungen.' : 'Keine offenen Meldungen.' }}
        </p>
      </BaseCard>

      <p v-if="error" class="text-error text-sm mt-4 text-center">{{ error }}</p>
      <div v-if="loading" class="skeleton h-48 w-full mt-4"></div>
      <BaseButton v-else-if="next" class="mt-4" size="sm" block @click="load">
        <AppIcon name="down" />
        Weitere laden
      </BaseButton>
    </div>
  </div>
  <BaseFooter />
</template>

<script>
import AppIcon from '@/components/common/AppIcon.vue'
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import BaseTabs from '@/components/common/BaseTabs.vue'
import CommentItem from '@/components/posts/CommentItem.vue'
import PostCard from '@/components/posts/PostCard.vue'
import { apiFetch } from '@/lib/api.js'

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
  },
  data() {
    return {
      breadcrumbs: [{ label: 'Moderation', to: '/moderation' }],
      tabs: [
        { key: 'open', label: 'Offen' },
        { key: 'resolved', label: 'Erledigt' },
      ],
      items: [],
      next: null,
      loading: false,
      error: null,
    }
  },
  computed: {
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
      const parts = [item.type === 'post' ? 'Feed' : 'Kommentar', `${item.report_count}× gemeldet`]
      if (this.resolved) parts.push(item.warned ? 'verwarnt' : 'verworfen')
      return parts.join(' · ')
    },
    reload() {
      this.items = []
      this.next = `/api/moderation/reports/?status=${this.status}`
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
        const response = await apiFetch(url)
        if (!response.ok) throw new Error()
        const data = await response.json()
        if (url !== this.next) return
        this.items.push(...data.results)
        this.next = data.next
      } catch {
        this.error = 'Meldungen konnten nicht geladen werden.'
      } finally {
        this.loading = false
      }
    },
  },
}
</script>

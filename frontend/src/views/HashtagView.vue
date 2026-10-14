<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div
    class="flex flex-col pb-8 px-6 max-h-[calc(100dvh-96px)] overflow-y-auto lg:max-h-none lg:overflow-y-visible lg:flex-1"
  >
    <div class="mx-auto w-full max-w-150 sm:pt-4">
      <BaseCard v-if="error" class="p-6">
        <p class="text-swissfy-muted">{{ error }}</p>
      </BaseCard>
      <div v-else-if="!hashtag" class="skeleton h-28 w-full"></div>
      <template v-else>
        <BaseCard class="flex items-center gap-4 p-6">
          <span
            class="flex size-16 shrink-0 items-center justify-center rounded-full bg-base-200 text-2xl font-bold"
          >
            #
          </span>
          <div class="flex min-w-0 flex-1 flex-col">
            <span class="truncate text-lg font-bold">#{{ hashtag.name }}</span>
            <span class="text-sm text-swissfy-muted">{{ hashtag.post_count }} Posts</span>
          </div>
          <BaseButton
            size="sm"
            :variant="hashtag.following ? 'neutral' : 'primary'"
            :disabled="busy"
            @click="toggleFollow"
          >
            <AppIcon :name="hashtag.following ? 'cross' : 'plus'" />
            {{ hashtag.following ? 'Entfolgen' : 'Folgen' }}
          </BaseButton>
        </BaseCard>

        <BaseTabs class="border-t-0" :tabs="tabs" :active="activeTab" />
        <PostList
          :key="`${hashtag.name}-${activeTab}`"
          class="mt-4"
          :url="postsUrl"
          :grid="activeTab === 'reels'"
          :reel-base="`/hashtags/${encodeURIComponent(hashtag.name)}/reels`"
          :empty-text="activeTab === 'reels' ? 'Noch keine Reels.' : 'Noch keine Posts.'"
        />
      </template>
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
import PostList from '@/components/posts/PostList.vue'
import { apiFetch } from '@/lib/api.js'

const TABS = [
  { key: 'posts', label: 'Posts', icon: 'list-timeline' },
  { key: 'reels', label: 'Reels', icon: 'clapperboard-play' },
]

export default {
  name: 'HashtagView',
  components: { AppIcon, BaseBreadcrumbs, BaseButton, BaseCard, BaseFooter, BaseTabs, PostList },
  data() {
    return {
      hashtag: null,
      error: null,
      busy: false,
      tabs: TABS,
    }
  },
  computed: {
    name() {
      return this.$route.params.name
    },
    apiBase() {
      return `/api/posts/hashtags/${encodeURIComponent(this.name)}`
    },
    breadcrumbs() {
      return [{ label: `#${this.name}`, to: this.$route.path }]
    },
    activeTab() {
      return TABS.some((tab) => tab.key === this.$route.query.tab) ? this.$route.query.tab : 'posts'
    },
    postsUrl() {
      return `${this.apiBase}/posts/${this.activeTab === 'reels' ? '?videos=1' : ''}`
    },
  },
  watch: {
    name: {
      immediate: true,
      async handler() {
        this.hashtag = null
        this.error = null
        const response = await apiFetch(`${this.apiBase}/`)
        if (response.ok) {
          this.hashtag = await response.json()
        } else {
          this.error =
            response.status === 404
              ? 'Zu diesem Hashtag gibt es noch keine Posts.'
              : 'Hashtag konnte nicht geladen werden.'
        }
      },
    },
  },
  methods: {
    async toggleFollow() {
      this.busy = true
      try {
        const response = await apiFetch(`${this.apiBase}/follow/`, {
          method: this.hashtag.following ? 'DELETE' : 'PUT',
        })
        if (response.ok) this.hashtag = await response.json()
      } finally {
        this.busy = false
      }
    },
  },
}
</script>

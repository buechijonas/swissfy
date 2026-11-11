<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div
    class="flex flex-col pb-8 px-6 max-h-[calc(100dvh-var(--mobile-chrome-height))] overflow-y-auto lg:max-h-none lg:overflow-y-visible lg:flex-1"
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
            <span class="text-sm text-swissfy-muted">{{ hashtag.post_count }} Feeds</span>
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
          :empty-text="activeTab === 'reels' ? 'Noch keine Seeds.' : 'Noch keine Feeds.'"
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
import postsApi from '@/api/posts.js'

const TABS = [
  { key: 'posts', label: 'Feeds', icon: 'list-timeline' },
  { key: 'reels', label: 'Seeds', icon: 'clapperboard-play' },
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
    breadcrumbs() {
      return [{ label: `#${this.name}`, to: this.$route.path }]
    },
    activeTab() {
      return TABS.some((tab) => tab.key === this.$route.query.tab) ? this.$route.query.tab : 'posts'
    },
    postsUrl() {
      return postsApi.hashtagPostsUrl(this.name, this.activeTab === 'reels' ? { videos: 1 } : null)
    },
  },
  watch: {
    name: {
      immediate: true,
      async handler() {
        this.hashtag = null
        this.error = null
        try {
          this.hashtag = await postsApi.hashtag(this.name)
        } catch (error) {
          this.error =
            error.status === 404
              ? 'Zu diesem Hashtag gibt es noch keine Feeds.'
              : 'Hashtag konnte nicht geladen werden.'
        }
      },
    },
  },
  methods: {
    async toggleFollow() {
      this.busy = true
      try {
        const follow = this.hashtag.following ? postsApi.unfollowHashtag : postsApi.followHashtag
        this.hashtag = await follow(this.name).catch(() => this.hashtag)
      } finally {
        this.busy = false
      }
    },
  },
}
</script>

<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div
    class="flex max-h-[calc(100dvh-var(--mobile-chrome-height))] flex-col overflow-y-auto px-6 pb-8 lg:max-h-none lg:flex-1 lg:overflow-y-visible"
  >
    <div class="mx-auto w-full max-w-150 sm:pt-4">
      <BaseCard v-if="error" class="p-6">
        <p class="text-app-muted">{{ error }}</p>
      </BaseCard>
      <div v-else-if="!hashtag" class="h-28 w-full skeleton"></div>
      <template v-else>
        <BaseCard class="flex items-center gap-4 p-6">
          <span
            class="flex size-16 shrink-0 items-center justify-center rounded-full bg-base-200 text-2xl font-bold"
          >
            #
          </span>
          <div class="flex min-w-0 flex-1 flex-col">
            <span class="truncate text-lg font-bold">#{{ hashtag.name }}</span>
            <span class="text-sm text-app-muted">{{
              $t('hashtag.postCount', { count: hashtag.post_count })
            }}</span>
          </div>
          <BaseButton
            size="sm"
            :variant="hashtag.following ? 'neutral' : 'primary'"
            :disabled="busy"
            @click="toggleFollow"
          >
            <AppIcon :name="hashtag.following ? 'cross' : 'plus'" />
            {{ hashtag.following ? $t('hashtag.unfollow') : $t('hashtag.follow') }}
          </BaseButton>
        </BaseCard>

        <BaseTabs class="border-t-0" :tabs="tabs" :active="activeTab" />
        <PostList
          :key="`${hashtag.name}-${activeTab}`"
          class="mt-4"
          :url="postsUrl"
          :grid="activeTab === 'reels'"
          :reel-base="`/hashtags/${encodeURIComponent(hashtag.name)}/reels`"
          :empty-text="activeTab === 'reels' ? $t('hashtag.noReels') : $t('hashtag.noPosts')"
        />
      </template>
    </div>
  </div>
  <BaseFooter />
</template>

<script>
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import BaseCard from '@core/components/BaseCard.vue'
import postsApi from '@/api/posts.js'
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import BaseTabs from '@/components/common/BaseTabs.vue'
import PostList from '@/components/posts/PostList.vue'
import { t } from '@/i18n.js'

function hashtagTabs() {
  return [
    { key: 'posts', label: t('hashtag.posts'), icon: 'list-timeline' },
    { key: 'reels', label: t('hashtag.reels'), icon: 'clapperboard-play' },
  ]
}

export default {
  name: 'HashtagView',
  components: { AppIcon, BaseBreadcrumbs, BaseButton, BaseCard, BaseFooter, BaseTabs, PostList },
  data() {
    return {
      hashtag: null,
      error: null,
      busy: false,
    }
  },
  computed: {
    tabs() {
      return hashtagTabs()
    },
    name() {
      return this.$route.params.name
    },
    breadcrumbs() {
      return [{ label: `#${this.name}`, to: this.$route.path }]
    },
    activeTab() {
      return hashtagTabs().some((tab) => tab.key === this.$route.query.tab)
        ? this.$route.query.tab
        : 'posts'
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
          this.error = error.status === 404 ? t('hashtag.empty') : t('hashtag.loadFailed')
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

<template>
  <ReelFeed v-if="reel" :initial-posts="[post]" @deleted="$router.push('/')" />
  <template v-else>
    <BaseBreadcrumbs :items="breadcrumbs" />
    <div
      class="flex flex-col pb-8 px-6 max-h-[calc(100dvh-var(--mobile-chrome-height))] overflow-y-auto lg:max-h-none lg:overflow-y-visible lg:flex-1"
    >
      <div class="mx-auto w-full max-w-150 sm:pt-4">
        <BaseCard v-if="error" class="p-6">
          <p class="text-swissfy-muted">{{ error }}</p>
        </BaseCard>
        <div v-else-if="!post" class="skeleton h-96 w-full"></div>
        <template v-else>
          <PostCard
            :post="post"
            detail
            edge-to-edge
            :moderation="moderation"
            @deleted="$router.push('/')"
          />
          <CommentSection
            class="mt-4"
            :url="commentsUrl"
            :moderation="moderation"
            @created="post.comment_count += 1"
            @deleted="post.comment_count = $event.comment_count"
          >
            <template v-if="moderation" #composer>
              <ModerationPanel kind="posts" :target-id="id" :details="details" />
            </template>
          </CommentSection>
        </template>
      </div>
    </div>
  </template>
  <BaseFooter :dark="reel" />
</template>

<script>
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import ModerationPanel from '@/components/moderation/ModerationPanel.vue'
import CommentSection from '@/components/posts/CommentSection.vue'
import PostCard from '@/components/posts/PostCard.vue'
import ReelFeed from '@/components/posts/ReelFeed.vue'
import moderationApi from '@/api/moderation.js'
import postsApi from '@/api/posts.js'

export default {
  name: 'PostView',
  components: {
    BaseBreadcrumbs,
    BaseCard,
    BaseFooter,
    CommentSection,
    ModerationPanel,
    PostCard,
    ReelFeed,
  },
  props: {
    moderation: { type: Boolean, default: false },
  },
  data() {
    return {
      post: null,
      details: null,
      error: null,
    }
  },
  computed: {
    id() {
      return this.$route.params.id
    },
    commentsUrl() {
      return this.moderation
        ? moderationApi.childrenUrl('posts', this.id)
        : postsApi.commentsUrl(this.id)
    },
    reel() {
      return Boolean(this.post?.video) && !this.moderation
    },
    breadcrumbs() {
      const post = { label: 'Feed', to: this.$route.path }
      return this.moderation ? [{ label: 'Moderation', to: '/moderation' }, post] : [post]
    },
  },
  async created() {
    let data
    try {
      data = this.moderation
        ? await moderationApi.get('posts', this.id)
        : await postsApi.get(this.id)
    } catch (error) {
      this.error =
        error.status === 404 ? 'Feed nicht gefunden.' : 'Feed konnte nicht geladen werden.'
      return
    }
    if (this.moderation) {
      const { post, ...details } = data
      this.details = details
      this.post = post
    } else {
      this.post = data
    }
  },
}
</script>

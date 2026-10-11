<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div
    class="flex flex-col pb-8 px-6 max-h-[calc(100dvh-96px)] overflow-y-auto lg:max-h-none lg:overflow-y-visible lg:flex-1"
  >
    <div class="mx-auto w-full max-w-150 sm:pt-4">
      <BaseCard v-if="error" class="p-6">
        <p class="text-swissfy-muted">{{ error }}</p>
      </BaseCard>
      <div v-else-if="!post" class="skeleton h-96 w-full"></div>
      <template v-else>
        <PostCard :post="post" detail edge-to-edge @deleted="$router.push('/')" />
        <CommentSection
          class="mt-4"
          :url="`${apiBase}/comments/`"
          @created="post.comment_count += 1"
          @deleted="post.comment_count = $event.comment_count"
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
import CommentSection from '@/components/posts/CommentSection.vue'
import PostCard from '@/components/posts/PostCard.vue'
import { apiFetch } from '@/lib/api.js'

export default {
  name: 'PostView',
  components: { BaseBreadcrumbs, BaseCard, BaseFooter, CommentSection, PostCard },
  data() {
    return {
      post: null,
      error: null,
    }
  },
  computed: {
    apiBase() {
      return `/api/posts/${this.$route.params.id}`
    },
    breadcrumbs() {
      return [{ label: 'Post', to: this.$route.path }]
    },
  },
  async created() {
    const response = await apiFetch(`${this.apiBase}/`)
    if (!response.ok) {
      this.error =
        response.status === 404 ? 'Post nicht gefunden.' : 'Post konnte nicht geladen werden.'
      return
    }
    this.post = await response.json()
  },
}
</script>

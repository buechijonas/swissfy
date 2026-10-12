<template>
  <BaseCard v-if="hashtags.length" tag="ul" class="mb-4 divide-y divide-swissfy-border">
    <li v-for="hashtag in hashtags" :key="hashtag.name">
      <RouterLink
        :to="hashtagLink(hashtag.name)"
        class="flex items-center gap-4 px-6 py-3 hover:bg-base-200"
      >
        <span
          class="flex size-12 shrink-0 items-center justify-center rounded-full bg-base-200 text-xl font-bold"
        >
          #
        </span>
        <div class="flex min-w-0 flex-1 flex-col">
          <span class="truncate font-bold">#{{ hashtag.name }}</span>
          <span class="truncate text-sm text-swissfy-muted">{{ hashtag.post_count }} Posts</span>
        </div>
        <span v-if="hashtag.following" class="text-sm text-swissfy-muted">Gefolgt</span>
      </RouterLink>
    </li>
  </BaseCard>
</template>

<script>
import { RouterLink } from 'vue-router'
import BaseCard from '@/components/common/BaseCard.vue'
import { apiFetch } from '@/lib/api.js'
import { hashtagLink } from '@/lib/hashtags.js'

export default {
  name: 'HashtagList',
  components: { RouterLink, BaseCard },
  props: {
    query: { type: String, default: '' },
  },
  data() {
    return { hashtags: [] }
  },
  watch: {
    query: {
      immediate: true,
      async handler(query) {
        if (!query) {
          this.hashtags = []
          return
        }
        const params = new URLSearchParams({ q: query })
        const response = await apiFetch(`/api/posts/hashtags/?${params}`)
        const hashtags = response.ok ? await response.json() : []
        if (query === this.query) this.hashtags = hashtags
      },
    },
  },
  methods: {
    hashtagLink,
  },
}
</script>

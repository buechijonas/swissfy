<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div
    class="flex flex-col pb-8 px-6 max-h-[calc(100dvh-48px)] overflow-y-auto lg:max-h-none lg:overflow-y-visible lg:flex-1"
  >
    <div class="mx-auto w-full max-w-150">
      <h2 class="text-xl font-light my-4">Suchen</h2>

      <BaseCard v-if="users.length" tag="ul" class="divide-y divide-swissfy-border">
        <li v-for="user in users" :key="user.username">
          <RouterLink
            :to="`/profile/${encodeURIComponent(user.username)}`"
            class="flex items-center gap-4 px-6 py-3 hover:bg-swissfy-highlight"
          >
            <img class="size-12 shrink-0" :src="avatarSrc(user)" alt="" />
            <div class="flex flex-col min-w-0">
              <span class="font-bold truncate">{{ fullName(user) || user.username }}</span>
              <span class="text-swissfy-muted text-sm truncate">@{{ user.username }}</span>
            </div>
          </RouterLink>
        </li>
      </BaseCard>

      <BaseCard v-else-if="!hasMore && !loading" class="p-6">
        <p class="text-swissfy-muted">Noch keine anderen User.</p>
      </BaseCard>

      <p v-if="error" class="text-error text-sm mt-4 text-center">{{ error }}</p>

      <div v-if="loading" class="flex flex-col gap-3 mt-3">
        <div v-for="n in 3" :key="n" class="flex items-center gap-4 px-6 py-3">
          <div class="skeleton size-12 rounded-full"></div>
          <div class="flex flex-col gap-2">
            <div class="skeleton h-4 w-40"></div>
            <div class="skeleton h-3 w-24"></div>
          </div>
        </div>
      </div>

      <div ref="sentinel" class="h-px"></div>
    </div>
  </div>
  <BaseFooter />
</template>

<script>
import { RouterLink } from 'vue-router'
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import { icons } from '@/assets/icons.js'
import { avatars } from '@/assets/images.js'
import { apiFetch } from '@/lib/api.js'

export default {
  name: 'SearchView',
  components: { RouterLink, BaseBreadcrumbs, BaseCard, BaseFooter },
  data() {
    return {
      breadcrumbs: [{ label: 'Suchen', to: '/search' }],
      users: [],
      page: 0,
      hasMore: true,
      loading: false,
      error: null,
    }
  },
  mounted() {
    // Loads the next page whenever the end of the list scrolls into view.
    this.observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting) this.loadMore()
    })
    this.observer.observe(this.$refs.sentinel)
  },
  beforeUnmount() {
    this.observer.disconnect()
  },
  methods: {
    async loadMore() {
      if (this.loading || !this.hasMore || this.error) return
      this.loading = true
      try {
        const response = await apiFetch(`/api/social/profiles/?page=${this.page + 1}`)
        if (!response.ok) {
          this.error = 'User konnten nicht geladen werden.'
          return
        }
        const data = await response.json()
        this.users.push(...data.results)
        this.page += 1
        this.hasMore = data.next !== null
      } finally {
        this.loading = false
      }
      // A page too short to fill the screen leaves the sentinel visible, which
      // fires no new event. Re-observing reports its current visibility again.
      await this.$nextTick()
      this.observer.unobserve(this.$refs.sentinel)
      this.observer.observe(this.$refs.sentinel)
    },
    avatarSrc(user) {
      return avatars[user.avatar] ?? icons.user
    },
    fullName(user) {
      return [user.first_name, user.last_name].filter(Boolean).join(' ')
    },
  },
}
</script>

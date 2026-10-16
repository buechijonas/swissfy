<template>
  <BaseCard v-if="users.length" tag="ul" class="divide-y divide-swissfy-border">
    <li v-for="user in users" :key="user.username">
      <UserRow :user="user" :to="linkTo(user)" />
    </li>
  </BaseCard>

  <BaseCard v-else-if="!hasMore && !loading" class="p-6">
    <p class="text-swissfy-muted">
      {{ query ? 'Keine User gefunden.' : emptyText }}
    </p>
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
</template>

<script>
import BaseCard from '@/components/common/BaseCard.vue'
import UserRow from '@/components/common/UserRow.vue'
import { apiFetch, extractErrorMessage } from '@/lib/api.js'

export default {
  name: 'UserList',
  components: { BaseCard, UserRow },
  props: {
    linkTo: { type: Function, required: true },
    query: { type: String, default: '' },
    url: { type: String, default: '/api/social/profiles/' },
    emptyText: { type: String, default: 'Noch keine anderen User.' },
  },
  data() {
    return {
      users: [],
      page: 0,
      hasMore: true,
      loading: false,
      error: null,
    }
  },
  watch: {
    query() {
      Object.assign(this, { users: [], page: 0, hasMore: true, error: null })
      this.loadMore()
    },
  },
  mounted() {
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
      const query = this.query
      try {
        const params = new URLSearchParams({ page: this.page + 1 })
        if (query) params.set('q', query)
        const response = await apiFetch(`${this.url}?${params}`)
        const data = await response.json().catch(() => null)
        if (query !== this.query) return
        if (!response.ok) {
          this.error = extractErrorMessage(data, 'User konnten nicht geladen werden.')
          return
        }
        this.users.push(...data.results)
        this.page += 1
        this.hasMore = data.next !== null
      } finally {
        this.loading = false
        if (query !== this.query) this.loadMore()
      }
      await this.$nextTick()
      this.observer.unobserve(this.$refs.sentinel)
      this.observer.observe(this.$refs.sentinel)
    },
  },
}
</script>

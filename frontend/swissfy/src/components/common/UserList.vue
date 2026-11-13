<template>
  <BaseCard v-if="users.length" tag="ul" class="divide-y divide-app-border">
    <li v-for="user in users" :key="user.username">
      <UserRow :user="user" :to="linkTo(user)">
        <template v-if="$slots.default" #default>
          <slot :user="user" />
        </template>
      </UserRow>
    </li>
  </BaseCard>

  <BaseCard v-else-if="!hasMore && !loading" class="p-6">
    <p class="text-app-muted">
      {{ query ? 'Keine User gefunden.' : emptyText }}
    </p>
  </BaseCard>

  <ErrorText :message="error" class="mt-4 text-center" />

  <div v-if="loading" class="flex flex-col gap-3 mt-3">
    <div v-for="n in 3" :key="n" class="flex items-center gap-4 px-6 py-3">
      <div class="skeleton size-12 rounded-full"></div>
      <div class="flex flex-col gap-2">
        <div class="skeleton h-4 w-40"></div>
        <div class="skeleton h-3 w-24"></div>
      </div>
    </div>
  </div>

  <div v-intersect="onSentinel" class="h-px"></div>
</template>

<script>
import ErrorText from '@core/components/ErrorText.vue'
import BaseCard from '@core/components/BaseCard.vue'
import UserRow from '@/components/common/UserRow.vue'
import api from '@core/api/client.js'
import profilesApi from '@/api/profiles.js'
import intersect from '@/directives/intersect.js'

export default {
  name: 'UserList',
  components: { BaseCard, UserRow, ErrorText },
  directives: { intersect },
  props: {
    linkTo: { type: Function, required: true },
    query: { type: String, default: '' },
    url: { type: String, default: profilesApi.listUrl() },
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
  methods: {
    onSentinel(visible) {
      if (visible) this.loadMore()
    },
    async loadMore() {
      if (this.loading || !this.hasMore || this.error) return
      this.loading = true
      const query = this.query
      try {
        const data = await api.get(this.url, { page: this.page + 1, ...(query && { q: query }) })
        if (query !== this.query) return
        this.users.push(...data.results)
        this.page += 1
        this.hasMore = data.next !== null
      } catch (error) {
        if (query !== this.query) return
        this.error = error.detail ?? 'User konnten nicht geladen werden.'
      } finally {
        this.loading = false
        if (query !== this.query) this.loadMore()
      }
    },
  },
}
</script>

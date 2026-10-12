<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div
    class="flex flex-col pb-8 px-6 max-h-[calc(100dvh-96px)] overflow-y-auto lg:max-h-none lg:overflow-y-visible lg:flex-1"
  >
    <div class="mx-auto w-full max-w-150 pt-4">
      <label class="input w-full mb-4">
        <AppIcon name="search" class="text-swissfy-muted" />
        <input
          v-model="term"
          type="search"
          class="grow"
          placeholder="Nach Benutzern oder #Hashtags suchen"
          autocomplete="off"
        />
      </label>
      <HashtagList :query="query" />
      <UserList
        v-if="!query.startsWith('#')"
        :query="query"
        :link-to="(user) => `/profile/${encodeURIComponent(user.username)}`"
      />
    </div>
  </div>
  <BaseFooter />
</template>

<script>
import AppIcon from '@/components/common/AppIcon.vue'
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import UserList from '@/components/common/UserList.vue'
import HashtagList from '@/components/posts/HashtagList.vue'

const DEBOUNCE_MS = 300
const MIN_QUERY_LENGTH = 2

export default {
  name: 'SearchView',
  components: { AppIcon, BaseBreadcrumbs, BaseFooter, HashtagList, UserList },
  data() {
    return {
      breadcrumbs: [{ label: 'Suchen', to: '/search' }],
      term: this.$route.query.q ?? '',
    }
  },
  computed: {
    query() {
      const query = (this.$route.query.q ?? '').trim()
      return query.length >= MIN_QUERY_LENGTH ? query : ''
    },
  },
  watch: {
    term(term) {
      clearTimeout(this.timer)
      this.timer = setTimeout(() => {
        this.$router.replace({ query: term.trim() ? { q: term.trim() } : {} })
      }, DEBOUNCE_MS)
    },
  },
  beforeUnmount() {
    clearTimeout(this.timer)
  },
}
</script>

<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div
    class="flex flex-col pb-8 px-6 max-h-[calc(100dvh-var(--mobile-chrome-height))] overflow-y-auto lg:max-h-none lg:overflow-y-visible lg:flex-1"
  >
    <div class="mx-auto w-full max-w-150 pt-4">
      <SearchField :placeholder="placeholder" />
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
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import SearchField from '@/components/common/SearchField.vue'
import UserList from '@/components/common/UserList.vue'
import HashtagList from '@/components/posts/HashtagList.vue'
import { searchQuery } from '@/lib/search.js'

export default {
  name: 'SearchView',
  components: { BaseBreadcrumbs, BaseFooter, HashtagList, SearchField, UserList },
  data() {
    return {
      breadcrumbs: [{ label: 'Suchen', to: '/search' }],
      placeholder: 'Nach Benutzern oder #Hashtags suchen',
    }
  },
  computed: {
    query() {
      return searchQuery(this.$route)
    },
  },
}
</script>

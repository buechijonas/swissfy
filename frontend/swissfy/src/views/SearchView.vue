<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div
    class="flex max-h-[calc(100dvh-var(--mobile-chrome-height))] flex-col overflow-y-auto px-6 pb-8 lg:max-h-none lg:flex-1 lg:overflow-y-visible"
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
import { t } from '@/i18n.js'
import { searchQuery } from '@/lib/search.js'

export default {
  name: 'SearchView',
  components: { BaseBreadcrumbs, BaseFooter, HashtagList, SearchField, UserList },
  computed: {
    placeholder() {
      return t('searchView.placeholder')
    },
    breadcrumbs() {
      return [{ label: t('searchView.title'), to: '/search' }]
    },
    query() {
      return searchQuery(this.$route)
    },
  },
}
</script>

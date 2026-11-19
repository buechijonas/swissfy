<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div
    class="flex max-h-[calc(100dvh-var(--mobile-chrome-height))] flex-col overflow-y-auto px-6 pb-8 lg:max-h-none lg:flex-1 lg:overflow-y-visible"
  >
    <div class="mx-auto w-full max-w-150 pt-4">
      <SearchField :placeholder="$t('connectionsView.searchPlaceholder')" />
      <UserList
        :key="url"
        :url="url"
        :query="query"
        :empty-text="connection.emptyText"
        :link-to="(user) => `/profile/${encodeURIComponent(user.username)}`"
      />
    </div>
  </div>
  <BaseFooter />
</template>

<script>
import profilesApi from '@/api/profiles.js'
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import SearchField from '@/components/common/SearchField.vue'
import UserList from '@/components/common/UserList.vue'
import { connections } from '@/data/connections.js'
import { t } from '@/i18n.js'
import { searchQuery } from '@/lib/search.js'
import { pageTitle } from '@/lib/title.js'

export default {
  name: 'ConnectionsView',
  components: { BaseBreadcrumbs, BaseFooter, SearchField, UserList },
  computed: {
    username() {
      return this.$route.params.username
    },
    connection() {
      return connections()[this.$route.params.connection]
    },
    url() {
      return profilesApi.connectionsUrl(this.username, this.$route.params.connection)
    },
    query() {
      return searchQuery(this.$route)
    },
    breadcrumbs() {
      return [
        {
          label: t('connectionsView.profile'),
          to: `/profile/${encodeURIComponent(this.username)}`,
        },
        { label: pageTitle(this.$route) },
      ]
    },
  },
}
</script>

<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div
    class="flex flex-col pb-8 px-6 max-h-[calc(100dvh-var(--mobile-chrome-height))] overflow-y-auto lg:max-h-none lg:overflow-y-visible lg:flex-1"
  >
    <div class="mx-auto w-full max-w-150 pt-4">
      <SearchField placeholder="Nach Benutzern suchen" />
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
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import SearchField from '@/components/common/SearchField.vue'
import UserList from '@/components/common/UserList.vue'
import profilesApi from '@/api/profiles.js'
import { CONNECTIONS } from '@/data/connections.js'
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
      return CONNECTIONS[this.$route.params.connection]
    },
    url() {
      return profilesApi.connectionsUrl(this.username, this.$route.params.connection)
    },
    query() {
      return searchQuery(this.$route)
    },
    breadcrumbs() {
      return [
        { label: 'Profil', to: `/profile/${encodeURIComponent(this.username)}` },
        { label: pageTitle(this.$route) },
      ]
    },
  },
}
</script>

<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div
    class="flex flex-col pb-8 px-6 max-h-[calc(100dvh-48px)] overflow-y-auto lg:max-h-none lg:overflow-y-visible lg:flex-1"
  >
    <div class="mx-auto w-full max-w-150 sm:pt-4">
      <UserList :link-to="(user) => `/profile/${encodeURIComponent(user.username)}`" />
    </div>
  </div>
  <BaseFooter />
</template>

<script>
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import UserList from '@/components/common/UserList.vue'

export default {
  name: 'SearchView',
  components: { BaseBreadcrumbs, BaseFooter, UserList },
  data() {
    return {
      breadcrumbs: [{ label: 'Suchen', to: '/search' }],
    }
  },
}
</script>

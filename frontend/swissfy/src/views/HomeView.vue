<template>
  <template v-if="authStore.isAuthenticated">
    <BaseBreadcrumbs :items="breadcrumbs">
      <template #actions>
        <AddButton :label="$t('home.post')" @click="$refs.composer.open()" />
      </template>
    </BaseBreadcrumbs>
    <div
      class="flex max-h-[calc(100dvh-var(--mobile-chrome-height))] flex-col overflow-y-auto px-6 pb-8 max-sm:pb-0 lg:max-h-none lg:flex-1 lg:overflow-y-visible"
    >
      <div class="mx-auto w-full max-w-150 pt-4 max-sm:pt-0">
        <PostList :url="feedUrl" edge-to-edge :empty-text="$t('home.empty')" />
      </div>
    </div>
    <CreateDialog ref="composer" />
    <BaseFooter />
  </template>
  <template v-else>
    <BaseBreadcrumbs :items="breadcrumbs" />
    <div
      class="flex max-h-[calc(100dvh-var(--mobile-chrome-height))] flex-col overflow-y-auto px-6 pb-8 max-sm:pb-0 lg:max-h-none lg:flex-1 lg:overflow-y-visible"
    >
      <div class="mx-auto w-full max-w-150 pt-4 max-sm:pt-0">
        <div class="my-16 flex flex-col">
          <h1 class="my-8 text-center text-title font-light">{{ $t('home.welcome') }}</h1>
          <p class="subtitle mx-auto font-light text-app-muted">swissfy.ch</p>
        </div>
        <PostList :url="globalUrl" edge-to-edge :empty-text="$t('home.noAnnouncements')" />
      </div>
    </div>
    <BaseFooter />
  </template>
</template>

<script>
import { mapStores } from 'pinia'
import postsApi from '@/api/posts.js'
import AddButton from '@/components/common/AddButton.vue'
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import CreateDialog from '@/components/posts/CreateDialog.vue'
import PostList from '@/components/posts/PostList.vue'
import { t } from '@/i18n.js'
import { useAuthStore } from '@/stores/auth.js'

export default {
  name: 'HomeView',
  components: { AddButton, BaseBreadcrumbs, BaseFooter, CreateDialog, PostList },
  data() {
    return {
      feedUrl: postsApi.feedUrl(),
      globalUrl: postsApi.globalUrl(),
    }
  },
  computed: {
    breadcrumbs() {
      return [{ label: t('home.home'), to: '/' }]
    },
    ...mapStores(useAuthStore),
  },
}
</script>

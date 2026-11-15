<template>
  <template v-if="authStore.isAuthenticated">
    <BaseBreadcrumbs :items="breadcrumbs">
      <template #actions>
        <AddButton :label="$t('home.post')" @click="$refs.composer.open()" />
      </template>
    </BaseBreadcrumbs>
    <div
      class="flex flex-col pb-8 px-6 max-sm:pb-0 max-h-[calc(100dvh-var(--mobile-chrome-height))] overflow-y-auto lg:max-h-none lg:overflow-y-visible lg:flex-1"
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
      class="flex flex-col pb-8 px-6 max-sm:pb-0 max-h-[calc(100dvh-var(--mobile-chrome-height))] overflow-y-auto lg:max-h-none lg:overflow-y-visible lg:flex-1"
    >
      <div class="mx-auto w-full max-w-150 pt-4 max-sm:pt-0">
        <div class="flex flex-col my-16">
          <h1 class="text-title my-8 text-center font-light">{{ $t('home.welcome') }}</h1>
          <p class="subtitle mx-auto text-app-muted font-light">swissfy.ch</p>
        </div>
        <PostList :url="globalUrl" edge-to-edge :empty-text="$t('home.noAnnouncements')" />
      </div>
    </div>
    <BaseFooter />
  </template>
</template>

<script>
import { mapStores } from 'pinia'
import AddButton from '@/components/common/AddButton.vue'
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import CreateDialog from '@/components/posts/CreateDialog.vue'
import PostList from '@/components/posts/PostList.vue'
import postsApi from '@/api/posts.js'
import { useAuthStore } from '@/stores/auth.js'
import { t } from '@/i18n.js'

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

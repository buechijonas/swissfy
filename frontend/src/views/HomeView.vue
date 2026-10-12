<template>
  <template v-if="authStore.isAuthenticated">
    <BaseBreadcrumbs :items="breadcrumbs">
      <template #actions>
        <AddButton label="Posten" @click="$refs.composer.open()" />
      </template>
    </BaseBreadcrumbs>
    <div
      class="flex flex-col pb-8 px-6 max-sm:pb-0 max-h-[calc(100dvh-96px)] overflow-y-auto lg:max-h-none lg:overflow-y-visible lg:flex-1"
    >
      <div class="mx-auto w-full max-w-150 pt-4 max-sm:pt-0">
        <PostList
          url="/api/posts/"
          edge-to-edge
          empty-text="Noch keine Posts. Folge Leuten oder Hashtags, um ihre Posts hier zu sehen."
        />
      </div>
    </div>
    <PostComposer ref="composer" @created="showOwnPosts" />
    <BaseFooter />
  </template>
  <template v-else>
    <BaseBreadcrumbs :items="breadcrumbs" />
    <div class="flex h-[calc(100dvh-139px)] lg:h-[calc(100dvh-192px)] px-6">
      <div class="flex flex-col mx-auto my-32">
        <h1 class="text-title my-8 text-center font-light">Herzlich Willkommen</h1>
        <p class="subtitle mx-auto text-swissfy-muted font-light">swissfy.ch</p>
      </div>
    </div>
    <BaseFooter />
  </template>
</template>

<script>
import AddButton from '@/components/common/AddButton.vue'
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import PostComposer from '@/components/posts/PostComposer.vue'
import PostList from '@/components/posts/PostList.vue'
import { useAuthStore } from '@/stores/auth.js'

export default {
  name: 'HomeView',
  components: { AddButton, BaseBreadcrumbs, BaseFooter, PostComposer, PostList },
  data() {
    return {
      breadcrumbs: [{ label: 'Home', to: '/' }],
    }
  },
  computed: {
    authStore() {
      return useAuthStore()
    },
  },
  methods: {
    showOwnPosts() {
      this.$router.push({ path: '/profile', query: { tab: 'activities' } })
    },
  },
}
</script>

<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div class="flex h-[calc(100dvh-192px)] px-6">
    <div class="flex flex-col mx-auto my-32">
      <h1 class="text-title my-8 text-center font-light">Herzlich Willkommen</h1>
      <div v-if="!authStore.ready" class="flex items-center gap-4 mx-auto mb-8">
        <div class="skeleton size-16 rounded-full"></div>
        <div class="flex flex-col gap-2">
          <div class="skeleton h-4 w-20"></div>
          <div class="skeleton h-4 w-28"></div>
        </div>
      </div>
      <div v-else-if="authStore.isAuthenticated" class="flex items-center gap-4 mx-auto mb-8">
        <img class="size-16" :src="avatarSrc" alt="" />
        <div class="flex flex-col gap-1 items-start">
          <span class="badge badge-primary badge-sm">{{
            authStore.user.role ?? 'Keine Rolle'
          }}</span>
          <span class="font-medium">{{ authStore.user.username }}</span>
        </div>
      </div>
      <p class="subtitle mx-auto text-swissfy-muted font-light">swissfy.ch</p>
    </div>
  </div>
  <BaseFooter />
</template>

<script>
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import { icons } from '@/assets/icons.js'
import { avatars } from '@/assets/images.js'
import { useAuthStore } from '@/stores/auth.js'

export default {
  name: 'HomeView',
  components: { BaseBreadcrumbs, BaseFooter },
  data() {
    return {
      breadcrumbs: [{ label: 'Home', to: '/' }],
    }
  },
  computed: {
    authStore() {
      return useAuthStore()
    },
    avatarSrc() {
      return avatars[this.authStore.user?.avatar] ?? icons.user
    },
  },
}
</script>

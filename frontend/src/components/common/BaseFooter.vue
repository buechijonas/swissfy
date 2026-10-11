<template>
  <footer
    class="sticky bottom-0 mt-auto flex h-12 w-full shrink-0 items-center justify-evenly bg-base-100 border-t border-swissfy-border border-solid lg:hidden"
  >
    <RouterLink
      v-for="item in footerItems"
      :key="item.key"
      :to="item.to"
      class="flex h-full items-center px-4 border-y-2 border-t-transparent"
      :class="
        $route.meta.activeNavigation === item.key ? 'border-b-current' : 'border-b-transparent'
      "
    >
      <img v-if="item.avatar && avatarSrc" class="size-6" :src="avatarSrc" :alt="item.label" />
      <AppIcon v-else :name="item.avatar ? 'user' : item.icon" :alt="item.label" class="size-6!" />
    </RouterLink>
  </footer>
</template>

<script>
import { RouterLink } from 'vue-router'
import AppIcon from '@/components/common/AppIcon.vue'
import { avatars } from '@/assets/images.js'
import { canAccess, navigationItems } from '@/data/navigation.js'
import { useAuthStore } from '@/stores/auth.js'

export default {
  name: 'BaseFooter',
  components: { RouterLink, AppIcon },
  computed: {
    authStore() {
      return useAuthStore()
    },
    footerItems() {
      return navigationItems.filter((item) => item.footer && canAccess(item, this.authStore))
    },
    avatarSrc() {
      return avatars[this.authStore.user?.avatar]
    },
  },
}
</script>

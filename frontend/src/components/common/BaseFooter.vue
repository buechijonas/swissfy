<template>
  <footer
    class="sticky bottom-0 mt-auto flex h-(--footer-height) pb-[env(safe-area-inset-bottom)] w-full shrink-0 items-center justify-evenly border-t border-solid lg:hidden"
    :class="dark ? 'bg-black border-white/15 text-white' : 'bg-base-100 border-swissfy-border'"
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
      <UserAvatar
        v-if="item.avatar && hasAvatar"
        class="size-6"
        :user="authStore.user"
        :alt="item.label"
      />
      <AppIcon v-else :name="item.avatar ? 'user' : item.icon" :alt="item.label" class="size-6!" />
    </RouterLink>
  </footer>
</template>

<script>
import { RouterLink } from 'vue-router'
import AppIcon from '@/components/common/AppIcon.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import { canAccess, navigationItems } from '@/data/navigation.js'
import { avatarSrc } from '@/lib/avatar.js'
import { useAuthStore } from '@/stores/auth.js'

export default {
  name: 'BaseFooter',
  components: { RouterLink, AppIcon, UserAvatar },
  props: {
    dark: { type: Boolean, default: false },
  },
  computed: {
    authStore() {
      return useAuthStore()
    },
    footerItems() {
      return navigationItems.filter((item) => item.footer && canAccess(item, this.authStore))
    },
    hasAvatar() {
      return Boolean(avatarSrc(this.authStore.user))
    },
  },
}
</script>

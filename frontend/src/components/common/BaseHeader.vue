<template>
  <div class="app-topbar relative z-20 h-12 w-full flex items-center bg-primary">
    <div
      class="lg:hidden flex items-center justify-center size-12 shrink-0 bg-base-100 text-base-content text-[1.2rem] font-normal"
    >
      {{ brandInitial }}
    </div>
    <span v-if="$route.meta.title" class="lg:hidden ml-4 truncate text-white">
      {{ $route.meta.title }}
    </span>
    <div class="flex h-full items-center gap-3 ml-auto px-4">
      <span v-if="!authStore.ready" class="skeleton h-4 w-24 max-lg:hidden"></span>
      <span v-else-if="authStore.isAuthenticated" class="text-white text-sm max-lg:hidden">
        {{ authStore.user.display_name }}
      </span>
      <RouterLink to="/settings" title="Einstellungen" :class="[iconLinkClass, 'max-lg:hidden']">
        <AppIcon name="settings" alt="Einstellungen" class="size-6!" />
      </RouterLink>
      <RouterLink
        v-if="authStore.isAuthenticated"
        to="/notifications"
        :title="notificationsLabel"
        :class="[iconLinkClass, 'lg:hidden']"
      >
        <AppIcon :name="notificationsIcon" :alt="notificationsLabel" class="size-6!" />
      </RouterLink>
      <label for="my-drawer-3" aria-label="Navigation öffnen" :class="[iconLinkClass, 'lg:hidden']">
        <AppIcon :name="drawerIcon" class="size-6!" />
      </label>
    </div>
  </div>
</template>

<script>
import { RouterLink } from 'vue-router'
import AppIcon from '@/components/common/AppIcon.vue'
import { isNavDrawerOpen } from '@/lib/navDrawer.js'
import { useAuthStore } from '@/stores/auth.js'
import { useNotificationsStore } from '@/stores/notifications.js'
import packageJson from '../../../package.json'

export default {
  name: 'BaseHeader',
  components: { RouterLink, AppIcon },
  data() {
    return {
      brandInitial: packageJson.name.charAt(0),
      iconLinkClass: 'flex h-full cursor-pointer items-center px-2 text-white',
    }
  },
  computed: {
    authStore() {
      return useAuthStore()
    },
    notificationsStore() {
      return useNotificationsStore()
    },
    notificationsIcon() {
      return this.notificationsStore.unread ? 'bell-notification-social-media' : 'bell'
    },
    notificationsLabel() {
      return this.notificationsStore.unread ? 'Neue Benachrichtigungen' : 'Benachrichtigungen'
    },
    drawerIcon() {
      return isNavDrawerOpen.value ? 'cross' : 'menu-burger'
    },
  },
}
</script>

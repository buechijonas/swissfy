<template>
  <div class="app-topbar relative z-20 h-12 w-full flex items-center bg-primary">
    <div
      class="lg:hidden flex items-center justify-center size-12 shrink-0 bg-base-100 text-base-content text-[1.2rem] font-normal"
    >
      {{ brandInitial }}
    </div>
    <span v-if="title" class="lg:hidden ml-4 truncate text-white">
      {{ title }}
    </span>
    <div class="flex h-full items-center gap-3 ml-auto px-4">
      <span v-if="!authStore.ready" class="skeleton h-4 w-24 max-lg:hidden"></span>
      <span v-else-if="authStore.isAuthenticated" class="text-white text-sm max-lg:hidden">
        {{ authStore.user.display_name }}
      </span>
      <RouterLink
        v-if="authStore.isAuthenticated"
        to="/notifications"
        :title="notificationsLabel"
        :class="[iconLinkClass, 'lg:hidden']"
      >
        <AppIcon :name="notificationsIcon" :alt="notificationsLabel" class="size-6!" />
      </RouterLink>
      <div
        class="dropdown dropdown-end h-full"
        :class="{ 'dropdown-open': isMenuOpen }"
        @keydown.esc="isMenuOpen = false"
      >
        <button
          type="button"
          aria-label="Menü"
          :aria-expanded="isMenuOpen"
          :class="iconLinkClass"
          @click="isMenuOpen = !isMenuOpen"
        >
          <AppIcon name="menu-burger" class="size-6!" />
        </button>
        <div v-if="isMenuOpen" class="fixed inset-0 z-30" @click="isMenuOpen = false"></div>
        <ul
          v-if="isMenuOpen"
          class="dropdown-content menu z-40 w-56 rounded-box border border-swissfy-border bg-base-100 p-1 text-base-content [--depth:0] [--menu-active-bg:transparent] [--menu-active-fg:var(--color-base-content)] [&_li>*:hover]:[--menu-active-bg:color-mix(in_oklab,var(--color-base-content)_10%,transparent)]"
        >
          <li>
            <RouterLink to="/settings" class="flex h-12 items-center gap-3">
              <AppIcon name="settings" class="size-6!" />
              <span>Einstellungen</span>
            </RouterLink>
          </li>
          <li v-if="authStore.isAuthenticated">
            <RouterLink to="/saved" class="flex h-12 items-center gap-3">
              <AppIcon name="bookmark" class="size-6!" />
              <span>Gespeichert</span>
            </RouterLink>
          </li>
          <li v-for="item in staffItems" :key="item.key" class="lg:hidden">
            <RouterLink :to="item.to" class="flex h-12 items-center gap-3">
              <AppIcon :name="item.icon" class="size-6!" />
              <span>{{ item.label }}</span>
            </RouterLink>
          </li>
          <li class="mt-1 border-t border-swissfy-border pt-1">
            <a :href="docsUrl" class="flex h-12 items-center gap-3">
              <AppIcon name="circle-book-open" class="size-6!" />
              <span>Dokumentation</span>
            </a>
          </li>
          <li>
            <a href="/api/auth/oidc/account/" class="flex h-12 items-center gap-3">
              <img :src="govexLogo" alt="" class="size-6" />
              <span>govex</span>
            </a>
          </li>
          <li v-if="authStore.ready" class="mt-1 border-t border-swissfy-border pt-1">
            <RouterLink
              :to="authStore.isAuthenticated ? '/logout' : '/login'"
              class="flex h-12 items-center gap-3"
            >
              <AppIcon :name="authStore.isAuthenticated ? 'exit' : 'enter'" class="size-6!" />
              <span>{{ authStore.isAuthenticated ? 'Abmelden' : 'Anmelden' }}</span>
            </RouterLink>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
import { RouterLink } from 'vue-router'
import AppIcon from '@/components/common/AppIcon.vue'
import govexLogo from '@core/assets/govex.svg'
import { docsUrl, isListed, navigationItems } from '@/data/navigation.js'
import { pageTitle } from '@/lib/title.js'
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
      docsUrl,
      govexLogo,
      isMenuOpen: false,
    }
  },
  computed: {
    authStore() {
      return useAuthStore()
    },
    notificationsStore() {
      return useNotificationsStore()
    },
    title() {
      return pageTitle(this.$route)
    },
    notificationsIcon() {
      return this.notificationsStore.unread ? 'bell-notification-social-media' : 'bell'
    },
    notificationsLabel() {
      return this.notificationsStore.unread ? 'Neue Benachrichtigungen' : 'Benachrichtigungen'
    },
    staffItems() {
      return navigationItems.filter((item) => item.roles && isListed(item, this.authStore))
    },
  },
  watch: {
    '$route.path'() {
      this.isMenuOpen = false
    },
  },
}
</script>

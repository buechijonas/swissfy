<template>
  <div class="app-topbar relative z-20 flex h-12 w-full items-center bg-primary">
    <div
      class="flex size-12 shrink-0 items-center justify-center bg-base-100 text-[1.2rem] font-normal text-base-content lg:hidden"
    >
      {{ brandInitial }}
    </div>
    <span v-if="title" class="ml-4 truncate text-white lg:hidden">
      {{ title }}
    </span>
    <div class="ml-auto flex h-full items-center gap-3 px-4">
      <span v-if="!authStore.ready" class="h-4 w-24 skeleton max-lg:hidden"></span>
      <span v-else-if="authStore.isAuthenticated" class="text-sm text-white max-lg:hidden">
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
          :aria-label="$t('header.menu')"
          :aria-expanded="isMenuOpen"
          :class="iconLinkClass"
          @click="isMenuOpen = !isMenuOpen"
        >
          <AppIcon name="menu-burger" class="size-6!" />
        </button>
        <div v-if="isMenuOpen" class="fixed inset-0 z-30" @click="isMenuOpen = false"></div>
        <ul
          v-if="isMenuOpen"
          class="app-menu menu dropdown-content z-40 w-56 rounded-box border border-app-border bg-base-100 p-1 text-base-content [--depth:0] [--menu-active-bg:transparent] [--menu-active-fg:var(--color-base-content)] [&_li>*:hover]:[--menu-active-bg:color-mix(in_oklab,var(--color-base-content)_10%,transparent)]"
          @click="isMenuOpen = false"
        >
          <li>
            <RouterLink to="/settings" class="flex h-12 items-center gap-3">
              <AppIcon name="settings" class="size-6!" />
              <span>{{ $t('header.settings') }}</span>
            </RouterLink>
          </li>
          <li v-if="authStore.isAuthenticated">
            <RouterLink to="/saved" class="flex h-12 items-center gap-3">
              <AppIcon name="bookmark" class="size-6!" />
              <span>{{ $t('header.saved') }}</span>
            </RouterLink>
          </li>
          <li v-for="item in staffItems" :key="item.key" class="lg:hidden">
            <RouterLink :to="item.to" class="flex h-12 items-center gap-3">
              <AppIcon :name="item.icon" class="size-6!" />
              <span>{{ item.label }}</span>
            </RouterLink>
          </li>
          <li class="mt-1 border-t border-app-border pt-1">
            <a :href="docsUrl" class="flex h-12 items-center gap-3">
              <AppIcon name="circle-book-open" class="size-6!" />
              <span>{{ $t('header.docs') }}</span>
            </a>
          </li>
          <li>
            <a href="/api/auth/oidc/account/" class="flex h-12 items-center gap-3">
              <img :src="govexLogo" alt="" class="size-6" />
              <span>govex</span>
            </a>
          </li>
          <li v-if="authStore.ready" class="mt-1 border-t border-app-border pt-1">
            <RouterLink
              :to="authStore.isAuthenticated ? '/logout' : '/login'"
              class="flex h-12 items-center gap-3"
            >
              <AppIcon :name="authStore.isAuthenticated ? 'exit' : 'enter'" class="size-6!" />
              <span>{{
                authStore.isAuthenticated ? $t('header.logout') : $t('header.login')
              }}</span>
            </RouterLink>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
import { mapStores } from 'pinia'
import { RouterLink } from 'vue-router'
import govexLogo from '@core/assets/govex.svg'
import AppIcon from '@core/components/AppIcon.vue'
import { docsUrl, isListed, navigationItems } from '@/data/navigation.js'
import { t } from '@/i18n.js'
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
    ...mapStores(useAuthStore),
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
      return this.notificationsStore.unread
        ? t('header.newNotifications')
        : t('header.notifications')
    },
    staffItems() {
      return navigationItems().filter((item) => item.permission && isListed(item, this.authStore))
    },
  },
  watch: {
    '$route.path'() {
      this.isMenuOpen = false
    },
  },
}
</script>

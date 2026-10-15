<template>
  <div class="app-nav col-start-2 row-start-1 hidden h-12 w-80 items-center pl-8 lg:flex">
    <h1 class="text-[1.2rem]">{{ appName }}</h1>
  </div>
  <div class="col-start-2 row-start-1 drawer drawer-end lg:drawer-open">
    <input id="my-drawer-3" v-model="isNavDrawerOpen" type="checkbox" class="drawer-toggle" />
    <div class="drawer-content"></div>
    <div
      class="app-nav drawer-side flex flex-col overflow-y-auto bg-base-100 top-12 h-[calc(100dvh-48px)]"
    >
      <label for="my-drawer-3" aria-label="close sidebar" class="drawer-overlay"></label>
      <ul class="menu w-full lg:w-80 p-4 gap-2">
        <template v-for="item in visibleNavigationItems" :key="item.key">
          <li
            v-if="item.divider"
            role="separator"
            class="pointer-events-none mx-4 my-2 h-px bg-swissfy-muted opacity-100!"
          ></li>
          <li
            :class="{
              'max-lg:hidden': item.footer || item.desktopOnly,
              'lg:hidden': item.mobileOnly,
            }"
          >
            <RouterLink
              :to="item.to"
              class="nav-item flex items-center gap-3 p-4"
              :class="{
                'active bg-swissfy-highlight text-primary shadow-none':
                  activeNavigation === item.key,
              }"
              @click="isNavDrawerOpen = false"
            >
              <UserAvatar v-if="item.avatar && hasAvatar" class="size-5" :user="authStore.user" />
              <AppIcon v-else :name="item.avatar ? 'user' : item.icon" class="size-5!" />
              <span>{{ item.label }}</span>
              <span v-if="item.badge?.()" class="badge badge-primary badge-sm ml-auto">
                {{ item.badge() }}
              </span>
            </RouterLink>
          </li>
        </template>
      </ul>
      <div v-if="!authStore.ready" class="mt-auto flex w-full flex-col gap-1 p-4">
        <div class="skeleton h-3 w-20"></div>
        <div class="skeleton mb-4 h-3 w-32"></div>
        <div class="skeleton h-10 w-full"></div>
      </div>
      <div v-else class="mt-auto p-4 w-full">
        <div class="mb-4 text-xs text-swissfy-muted font-light">
          <div>Version {{ version }}</div>
          <div>Created by NEOTYRA</div>
        </div>
        <BaseButton
          v-if="!authStore.isAuthenticated"
          variant="primary"
          block
          to="/login"
          @click="isNavDrawerOpen = false"
        >
          <AppIcon name="enter" />Anmelden
        </BaseButton>
        <BaseButton v-else variant="primary" block to="/logout" @click="isNavDrawerOpen = false">
          <AppIcon name="exit" />Abmelden
        </BaseButton>
      </div>
    </div>
  </div>
</template>

<script>
import { RouterLink } from 'vue-router'
import BaseButton from '@/components/common/BaseButton.vue'
import AppIcon from '@/components/common/AppIcon.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import { canAccess, navigationItems } from '@/data/navigation.js'
import { avatarSrc } from '@/lib/avatar.js'
import { isNavDrawerOpen } from '@/lib/navDrawer.js'
import { useAuthStore } from '@/stores/auth.js'
import packageJson from '../../../package.json'

export default {
  name: 'BaseNavigation',
  components: { RouterLink, BaseButton, AppIcon, UserAvatar },
  props: {
    activeNavigation: {
      type: String,
      default: null,
    },
  },
  data() {
    return {
      navigationItems,
      appName: packageJson.name,
      version: packageJson.version,
    }
  },
  computed: {
    authStore() {
      return useAuthStore()
    },
    visibleNavigationItems() {
      return this.navigationItems.filter((item) => canAccess(item, this.authStore))
    },
    hasAvatar() {
      return Boolean(avatarSrc(this.authStore.user))
    },
    isNavDrawerOpen: {
      get() {
        return isNavDrawerOpen.value
      },
      set(value) {
        isNavDrawerOpen.value = value
      },
    },
  },
}
</script>

<style>
@media (width >= 1024px) {
  .drawer.drawer-end.lg\:drawer-open {
    grid-template-columns: 0 max-content;
  }
}
</style>

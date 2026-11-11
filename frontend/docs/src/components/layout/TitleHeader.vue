<template>
  <div class="flex h-14 w-full items-center justify-end gap-3 px-6">
    <div class="mr-auto flex min-w-0 items-center gap-8">
      <RouterLink
        v-if="$route.name !== 'settings'"
        to="/"
        class="shrink-0 font-display text-3xl font-bold tracking-tighter text-docs-title"
      >
        {{ title }}
      </RouterLink>
    </div>
    <span v-if="!authStore.ready" class="skeleton h-4 w-24"></span>
    <span v-else-if="authStore.isAuthenticated" class="text-sm">
      {{ authStore.user.display_name }}
    </span>
    <div class="group dropdown dropdown-end" @keydown.esc="closeMenu">
      <div
        tabindex="0"
        role="button"
        aria-label="Menü"
        class="flex size-10 cursor-pointer items-center justify-center"
      >
        <AppIcon name="menu-burger" class="size-6!" />
      </div>
      <ul
        tabindex="0"
        class="dropdown-content menu invisible z-40 w-56 rounded-box border border-docs-border bg-base-100 p-1 [--menu-active-bg:transparent] [--menu-active-fg:var(--color-base-content)] [&_li>*:hover]:[--menu-active-bg:color-mix(in_oklab,var(--color-base-content)_10%,transparent)] group-focus-within:visible"
      >
        <li>
          <RouterLink
            v-if="$route.name !== 'settings'"
            to="/settings"
            class="flex h-12 items-center gap-3"
            @click="closeMenu"
          >
            <AppIcon name="settings" class="size-6!" />
            <span>Einstellungen</span>
          </RouterLink>
          <RouterLink v-else to="/" class="flex h-12 items-center gap-3" @click="closeMenu">
            <AppIcon name="circle-book-open" class="size-6!" />
            <span>Dokumentation</span>
          </RouterLink>
        </li>
        <li
          v-for="(target, index) in switches"
          :key="target.url"
          :class="{ 'mt-1 border-t border-docs-border pt-1': index === 0 }"
        >
          <a :href="target.url" class="flex h-12 items-center gap-3">
            <img src="/icons/icon.svg" alt="" class="size-6" />
            <span>{{ target.label }}</span>
          </a>
        </li>
        <li>
          <a href="/api/auth/oidc/account/" class="flex h-12 items-center gap-3">
            <img :src="govexLogo" alt="" class="size-6" />
            <span>govex</span>
          </a>
        </li>
        <li v-if="authStore.ready" class="mt-1 border-t border-docs-border pt-1">
          <button
            v-if="authStore.isAuthenticated"
            type="button"
            class="flex h-12 items-center gap-3"
            @click="logout"
          >
            <AppIcon name="exit" class="size-6!" />
            <span>Abmelden</span>
          </button>
          <button
            v-else
            type="button"
            class="flex h-12 items-center gap-3"
            @click="authStore.startGovexLogin()"
          >
            <AppIcon name="enter" class="size-6!" />
            <span>Anmelden</span>
          </button>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
import { RouterLink } from 'vue-router'
import AppIcon from '@/components/common/AppIcon.vue'
import govexLogo from '@core/assets/govex.svg'
import { closeMenu } from '@core/lib/menu.js'
import { useAuthStore } from '@/stores/auth.js'

export default {
  name: 'TitleHeader',
  components: { RouterLink, AppIcon },
  props: {
    title: { type: String, required: true },
    switches: { type: Array, default: () => [] },
  },
  data() {
    return { govexLogo }
  },
  computed: {
    authStore() {
      return useAuthStore()
    },
  },
  methods: {
    closeMenu,
    async logout() {
      closeMenu()
      await this.authStore.logout()
    },
  },
}
</script>

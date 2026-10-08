<template>
  <div class="app-topbar relative z-20 h-12 w-full flex items-center bg-primary">
    <div
      class="lg:hidden flex items-center justify-center size-12 shrink-0 bg-base-100 text-base-content text-[1.2rem] font-normal"
    >
      {{ brandInitial }}
    </div>
    <div class="flex items-center gap-3 ml-auto px-6">
      <span v-if="!authStore.ready" class="skeleton h-4 w-24 max-lg:hidden"></span>
      <span v-else-if="authStore.isAuthenticated" class="text-white text-sm max-lg:hidden">
        {{ authStore.user.display_name }}
      </span>
      <BaseButton
        class="max-lg:hidden"
        variant="ghost"
        shape="square"
        size="sm"
        to="/settings"
        aria-current-value="false"
      >
        <img :src="icons.settings" alt="Einstellungen" class="size-5 invert" />
      </BaseButton>
      <label
        for="my-drawer-3"
        aria-label="Navigation öffnen"
        class="btn btn-square btn-ghost btn-sm lg:hidden"
      >
        <img :src="drawerIcon" alt="" class="size-5 invert" />
      </label>
    </div>
  </div>
</template>

<script>
import BaseButton from '@/components/common/BaseButton.vue'
import { icons } from '@/assets/icons.js'
import { isNavDrawerOpen } from '@/lib/navDrawer.js'
import { useAuthStore } from '@/stores/auth.js'
import packageJson from '../../../package.json'

export default {
  name: 'BaseHeader',
  components: { BaseButton },
  data() {
    return { icons, brandInitial: packageJson.name.charAt(0) }
  },
  computed: {
    authStore() {
      return useAuthStore()
    },
    drawerIcon() {
      return isNavDrawerOpen.value ? icons.cross : icons['menu-burger']
    },
  },
}
</script>

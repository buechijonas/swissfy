<template>
  <footer
    class="app-footer sticky bottom-0 mt-auto h-(--footer-height) w-full shrink-0 border-t border-solid pb-[env(safe-area-inset-bottom)] lg:hidden"
    :class="
      dark ? 'app-footer-dark border-white/15 bg-black text-white' : 'border-app-border bg-base-100'
    "
  >
    <BubbleNavigation
      v-slot="nav"
      :active="$route.meta.activeNavigation"
      :track-width="bar?.width"
      :width-of="footerItems[0]?.key"
      :can-select="canSelect"
      @select="select"
    >
      <nav
        v-bounds="storeBar"
        v-pointer-drag="nav.handlers"
        class="app-footer-bar relative flex h-full items-center justify-evenly"
        :class="{ 'is-dragging': nav.dragging }"
        @dragstart.prevent
      >
        <span
          v-if="nav.bubble"
          v-wobble="nav.wobbles"
          class="app-bubble"
          :style="{
            left: `${nav.bubble.left}px`,
            width: `${nav.bubble.width}px`,
            '--stretch': nav.stretch,
          }"
        />
        <component
          :is="isLocked(item) ? 'span' : RouterLink"
          v-for="item in footerItems"
          :key="item.key"
          v-bounds="(box) => nav.storeBox(item.key, box)"
          v-bind="isLocked(item) ? { 'aria-disabled': 'true' } : { to: item.to }"
          class="relative flex h-full items-center border-y-2 border-t-transparent px-4"
          :class="[
            $route.meta.activeNavigation === item.key ? 'border-b-current' : 'border-b-transparent',
            { 'cursor-not-allowed text-app-muted': isLocked(item) },
          ]"
        >
          <UserAvatar
            v-if="item.avatar && hasAvatar"
            class="size-6"
            :user="authStore.user"
            :alt="item.label"
          />
          <AppIcon
            v-else
            :name="item.avatar ? 'user' : item.icon"
            :alt="item.label"
            class="size-6!"
          />
          <span v-if="item.badge?.()" class="absolute top-2 right-2 badge badge-xs badge-primary">
            {{ item.badge() }}
          </span>
        </component>
      </nav>
    </BubbleNavigation>
  </footer>
</template>

<script>
import filter from 'lodash-es/filter'
import find from 'lodash-es/find'
import { mapStores } from 'pinia'
import { RouterLink } from 'vue-router'
import AppIcon from '@core/components/AppIcon.vue'
import BubbleNavigation from '@/components/common/BubbleNavigation.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import { isListed, isLocked, navigationItems } from '@/data/navigation.js'
import bounds from '@/directives/bounds.js'
import pointerDrag from '@/directives/pointerDrag.js'
import wobble from '@/directives/wobble.js'
import { avatarSrc } from '@/lib/avatar.js'
import { useAuthStore } from '@/stores/auth.js'

export default {
  name: 'BaseFooter',
  components: { RouterLink, AppIcon, BubbleNavigation, UserAvatar },
  directives: { bounds, pointerDrag, wobble },
  props: {
    dark: { type: Boolean, default: false },
  },
  data() {
    return {
      RouterLink,
      bar: null,
    }
  },
  computed: {
    ...mapStores(useAuthStore),
    footerItems() {
      return filter(navigationItems(), (item) => item.footer && isListed(item, this.authStore))
    },
    hasAvatar() {
      return Boolean(avatarSrc(this.authStore.user))
    },
  },
  methods: {
    isLocked(item) {
      return isLocked(item, this.authStore)
    },
    storeBar(box) {
      this.bar = box
    },
    itemOf(key) {
      return find(this.footerItems, { key })
    },
    canSelect(key) {
      const item = this.itemOf(key)
      return Boolean(item) && !this.isLocked(item)
    },
    select(key) {
      this.$router.push(this.itemOf(key).to)
    },
  },
}
</script>

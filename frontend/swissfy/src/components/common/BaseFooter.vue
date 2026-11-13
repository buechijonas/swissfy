<template>
  <footer
    class="app-footer sticky bottom-0 mt-auto h-(--footer-height) pb-[env(safe-area-inset-bottom)] w-full shrink-0 border-t border-solid lg:hidden"
    :class="
      dark ? 'app-footer-dark bg-black border-white/15 text-white' : 'bg-base-100 border-app-border'
    "
  >
    <nav
      v-bounds="storeBar"
      v-pointer-drag="{ grab, move: drag, release, cancel }"
      class="app-footer-bar relative flex h-full items-center justify-evenly"
      :class="{ 'is-dragging': dragging }"
      @dragstart.prevent
    >
      <span
        v-if="bubble"
        v-wobble="wobbles"
        class="app-bubble"
        :style="{ left: `${bubble.left}px`, width: `${bubble.width}px`, '--stretch': stretch }"
      />
      <component
        :is="isLocked(item) ? 'span' : RouterLink"
        v-for="item in footerItems"
        :key="item.key"
        v-bounds="(box) => storeBox(item.key, box)"
        v-bind="isLocked(item) ? { 'aria-disabled': 'true' } : { to: item.to }"
        class="relative flex h-full items-center px-4 border-y-2 border-t-transparent"
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
        <span v-if="item.badge?.()" class="badge badge-primary badge-xs absolute top-2 right-2">
          {{ item.badge() }}
        </span>
      </component>
    </nav>
  </footer>
</template>

<script>
import { mapStores } from 'pinia'
import { RouterLink } from 'vue-router'
import filter from 'lodash-es/filter'
import find from 'lodash-es/find'
import head from 'lodash-es/head'
import AppIcon from '@core/components/AppIcon.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import { isListed, isLocked, navigationItems } from '@/data/navigation.js'
import bounds from '@/directives/bounds.js'
import pointerDrag from '@/directives/pointerDrag.js'
import wobble from '@/directives/wobble.js'
import { avatarSrc } from '@/lib/avatar.js'
import bubbleNavigationMixin from '@/mixins/bubbleNavigationMixin.js'
import { useAuthStore } from '@/stores/auth.js'

export default {
  name: 'BaseFooter',
  components: { RouterLink, AppIcon, UserAvatar },
  directives: { bounds, pointerDrag, wobble },
  mixins: [bubbleNavigationMixin],
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
      return filter(navigationItems, (item) => item.footer && isListed(item, this.authStore))
    },
    hasAvatar() {
      return Boolean(avatarSrc(this.authStore.user))
    },
    activeKey() {
      return this.$route.meta.activeNavigation
    },
    trackWidth() {
      return this.bar.width
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
    dragWidth() {
      return this.boxes[head(this.footerItems).key].width
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

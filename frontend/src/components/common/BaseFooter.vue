<template>
  <footer
    class="app-footer sticky bottom-0 mt-auto h-(--footer-height) pb-[env(safe-area-inset-bottom)] w-full shrink-0 border-t border-solid lg:hidden"
    :class="
      dark
        ? 'app-footer-dark bg-black border-white/15 text-white'
        : 'bg-base-100 border-swissfy-border'
    "
  >
    <nav
      ref="bar"
      class="app-footer-bar relative flex h-full items-center justify-evenly"
      :class="{ 'is-dragging': dragging }"
      @pointerdown="grab"
      @pointermove="drag"
      @pointerup="release"
      @pointercancel="cancel"
      @dragstart.prevent
    >
      <span
        v-if="bubble"
        ref="bubble"
        class="app-bubble"
        :style="{ left: `${bubble.left}px`, width: `${bubble.width}px`, '--stretch': stretch }"
      />
      <RouterLink
        v-for="item in footerItems"
        :key="item.key"
        ref="links"
        :to="item.to"
        class="relative flex h-full items-center px-4 border-y-2 border-t-transparent"
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
        <AppIcon
          v-else
          :name="item.avatar ? 'user' : item.icon"
          :alt="item.label"
          class="size-6!"
        />
        <span v-if="item.badge?.()" class="badge badge-primary badge-xs absolute top-2 right-2">
          {{ item.badge() }}
        </span>
      </RouterLink>
    </nav>
  </footer>
</template>

<script>
import { RouterLink } from 'vue-router'
import AppIcon from '@/components/common/AppIcon.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import { canAccess, navigationItems } from '@/data/navigation.js'
import { avatarSrc } from '@/lib/avatar.js'
import { wobble } from '@/lib/bubble.js'
import { design } from '@/lib/preferences.js'
import { useAuthStore } from '@/stores/auth.js'

export default {
  name: 'BaseFooter',
  components: { RouterLink, AppIcon, UserAvatar },
  props: {
    dark: { type: Boolean, default: false },
  },
  data() {
    return {
      bubble: null,
      dragging: false,
      stretch: 1,
      last: null,
    }
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
    activeIndex() {
      return this.footerItems.findIndex((item) => item.key === this.$route.meta.activeNavigation)
    },
  },
  watch: {
    activeIndex() {
      this.$nextTick(() => {
        this.placeBubble()
        this.wobble()
      })
    },
  },
  mounted() {
    this.placeBubble()
    window.addEventListener('resize', this.placeBubble)
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.placeBubble)
  },
  methods: {
    linkAt(index) {
      return this.$refs.links?.[index]?.$el
    },
    placeBubble() {
      const link = this.linkAt(this.activeIndex)
      this.bubble = link && { left: link.offsetLeft, width: link.offsetWidth }
    },
    wobble() {
      wobble(this.$refs.bubble)
    },
    grab(event) {
      if (design.value !== 'glass') return
      this.dragging = true
      this.last = null
      event.currentTarget.setPointerCapture(event.pointerId)
      this.drag(event)
    },
    drag(event) {
      if (!this.dragging) return
      const bar = this.$refs.bar.getBoundingClientRect()
      const width = this.linkAt(0).offsetWidth
      const left = Math.min(Math.max(event.clientX - bar.left - width / 2, 0), bar.width - width)
      this.bubble = { left, width }
      if (this.last) {
        const speed =
          Math.abs(event.clientX - this.last.x) / (event.timeStamp - this.last.time || 1)
        this.stretch = 1 + Math.min(speed * 0.3, 0.45)
      }
      this.last = { x: event.clientX, time: event.timeStamp }
    },
    cancel() {
      this.dragging = false
      this.stretch = 1
      this.placeBubble()
    },
    release(event) {
      if (!this.dragging) return
      this.dragging = false
      this.stretch = 1
      const index = this.footerItems.findIndex((_, i) => {
        const { left, right } = this.linkAt(i).getBoundingClientRect()
        return event.clientX >= left && event.clientX <= right
      })
      if (index === -1) return this.placeBubble()
      const link = this.linkAt(index)
      this.bubble = { left: link.offsetLeft, width: link.offsetWidth }
      if (index === this.activeIndex) this.wobble()
      this.$router.push(this.footerItems[index].to)
    },
  },
}
</script>

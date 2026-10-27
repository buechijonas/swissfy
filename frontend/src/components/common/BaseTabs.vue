<template>
  <BaseCard
    ref="list"
    role="tablist"
    class="app-tabs tabs relative flex-nowrap overflow-x-auto px-2 [scrollbar-width:none]"
    :class="{ 'is-dragging': dragging, 'is-scrollable': scrollable }"
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
      v-for="tab in tabs"
      :key="tab.key"
      ref="links"
      role="tab"
      class="tab relative h-12 shrink-0 whitespace-nowrap border-y-2 border-t-transparent"
      :class="[
        active === tab.key ? 'tab-active border-b-primary' : 'border-b-transparent',
        { 'flex-1': tab.icon },
      ]"
      :aria-selected="active === tab.key"
      :title="tab.icon && tab.label"
      :to="tabLink(tab)"
      replace
    >
      <AppIcon v-if="tab.icon" :name="tab.icon" :alt="tab.label" class="size-5!" />
      <template v-else>{{ tab.label }}</template>
    </RouterLink>
  </BaseCard>
</template>

<script>
import { RouterLink } from 'vue-router'
import AppIcon from '@/components/common/AppIcon.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import { wobble } from '@/lib/bubble.js'
import { design } from '@/lib/preferences.js'

export default {
  name: 'BaseTabs',
  components: { RouterLink, AppIcon, BaseCard },
  props: {
    tabs: { type: Array, required: true },
    active: { type: String, required: true },
  },
  data() {
    return {
      bubble: null,
      dragging: false,
      scrollable: false,
      stretch: 1,
      last: null,
      observer: null,
    }
  },
  computed: {
    activeIndex() {
      return this.tabs.findIndex((tab) => tab.key === this.active)
    },
  },
  watch: {
    activeIndex() {
      this.$nextTick(() => {
        this.placeBubble()
        wobble(this.$refs.bubble)
      })
    },
  },
  mounted() {
    this.placeBubble()
    this.observer = new ResizeObserver(() => this.placeBubble())
    this.observer.observe(this.$refs.list.$el)
  },
  beforeUnmount() {
    this.observer.disconnect()
  },
  methods: {
    tabLink(tab) {
      return { query: { tab: tab.key } }
    },
    linkAt(index) {
      return this.$refs.links?.[index]?.$el
    },
    indexAt(x) {
      return this.tabs.findIndex((_, i) => {
        const { left, right } = this.linkAt(i).getBoundingClientRect()
        return x >= left && x <= right
      })
    },
    placeBubble() {
      const list = this.$refs.list.$el
      this.scrollable = list.scrollWidth > list.clientWidth
      const link = this.linkAt(this.activeIndex)
      this.bubble = link && { left: link.offsetLeft, width: link.offsetWidth }
    },
    grab(event) {
      if (design.value !== 'glass') return
      if (this.scrollable && !this.linkAt(this.activeIndex)?.contains(event.target)) return
      this.dragging = true
      this.last = null
      event.currentTarget.setPointerCapture(event.pointerId)
      this.drag(event)
    },
    drag(event) {
      if (!this.dragging) return
      const list = this.$refs.list.$el
      const index = this.indexAt(event.clientX)
      const width = this.linkAt(index === -1 ? this.activeIndex : index).offsetWidth
      const x = event.clientX - list.getBoundingClientRect().left + list.scrollLeft
      const left = Math.min(Math.max(x - width / 2, 0), list.scrollWidth - width)
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
      const index = this.indexAt(event.clientX)
      if (index === -1) return this.placeBubble()
      const link = this.linkAt(index)
      this.bubble = { left: link.offsetLeft, width: link.offsetWidth }
      if (index === this.activeIndex) wobble(this.$refs.bubble)
      this.$router.replace(this.tabLink(this.tabs[index]))
    },
  },
}
</script>

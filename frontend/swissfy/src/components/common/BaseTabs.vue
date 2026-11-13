<template>
  <BaseCard
    v-bounds="storeList"
    v-pointer-drag="{ grab, move: drag, release, cancel }"
    role="tablist"
    class="app-tabs tabs relative flex-nowrap overflow-x-auto px-2 [scrollbar-width:none]"
    :class="{ 'is-dragging': dragging, 'is-scrollable': scrollable }"
    @dragstart.prevent
  >
    <span
      v-if="bubble"
      v-wobble="wobbles"
      class="app-bubble"
      :style="{ left: `${bubble.left}px`, width: `${bubble.width}px`, '--stretch': stretch }"
    />
    <RouterLink
      v-for="tab in tabs"
      :key="tab.key"
      v-bounds="(box) => storeBox(tab.key, box)"
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
import AppIcon from '@core/components/AppIcon.vue'
import BaseCard from '@core/components/BaseCard.vue'
import bounds from '@/directives/bounds.js'
import pointerDrag from '@/directives/pointerDrag.js'
import wobble from '@/directives/wobble.js'
import bubbleNavigationMixin from '@/mixins/bubbleNavigationMixin.js'

export default {
  name: 'BaseTabs',
  components: { RouterLink, AppIcon, BaseCard },
  directives: { bounds, pointerDrag, wobble },
  mixins: [bubbleNavigationMixin],
  props: {
    tabs: { type: Array, required: true },
    active: { type: String, required: true },
  },
  data() {
    return { list: null }
  },
  computed: {
    activeKey() {
      return this.active
    },
    scrollable() {
      return Boolean(this.list) && this.list.scrollWidth > this.list.clientWidth
    },
    trackWidth() {
      return this.list.scrollWidth
    },
  },
  methods: {
    tabLink(tab) {
      return { query: { tab: tab.key } }
    },
    storeList(box) {
      this.list = box
    },
    canGrab(x) {
      return !this.scrollable || this.keyAt(x) === this.active
    },
    dragWidth(x) {
      return this.boxes[this.keyAt(x) ?? this.active].width
    },
    select(key) {
      this.$router.replace(this.tabLink({ key }))
    },
  },
}
</script>

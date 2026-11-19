<template>
  <BubbleNavigation
    v-slot="nav"
    :active="active"
    :track-width="list?.scrollWidth"
    :grab-active-only="scrollable"
    @select="select"
  >
    <BaseCard
      v-bounds="storeList"
      v-pointer-drag="nav.handlers"
      role="tablist"
      class="app-tabs tabs relative [scrollbar-width:none] flex-nowrap overflow-x-auto px-2"
      :class="{ 'is-dragging': nav.dragging, 'is-scrollable': scrollable }"
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
      <RouterLink
        v-for="tab in tabs"
        :key="tab.key"
        v-bounds="(box) => nav.storeBox(tab.key, box)"
        role="tab"
        class="tab relative h-12 shrink-0 border-y-2 border-t-transparent whitespace-nowrap"
        :class="[
          active === tab.key ? 'border-b-primary tab-active' : 'border-b-transparent',
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
  </BubbleNavigation>
</template>

<script>
import { RouterLink } from 'vue-router'
import AppIcon from '@core/components/AppIcon.vue'
import BaseCard from '@core/components/BaseCard.vue'
import BubbleNavigation from '@/components/common/BubbleNavigation.vue'
import bounds from '@/directives/bounds.js'
import pointerDrag from '@/directives/pointerDrag.js'
import wobble from '@/directives/wobble.js'

export default {
  name: 'BaseTabs',
  components: { RouterLink, AppIcon, BaseCard, BubbleNavigation },
  directives: { bounds, pointerDrag, wobble },
  props: {
    tabs: { type: Array, required: true },
    active: { type: String, required: true },
  },
  data() {
    return { list: null }
  },
  computed: {
    scrollable() {
      return Boolean(this.list) && this.list.scrollWidth > this.list.clientWidth
    },
  },
  methods: {
    tabLink(tab) {
      return { query: { tab: tab.key } }
    },
    storeList(box) {
      this.list = box
    },
    select(key) {
      this.$router.replace(this.tabLink({ key }))
    },
  },
}
</script>

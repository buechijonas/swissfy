<template>
  <BaseCard role="tablist" class="tabs flex-nowrap overflow-x-auto px-2 [scrollbar-width:none]">
    <RouterLink
      v-for="tab in tabs"
      :key="tab.key"
      role="tab"
      class="tab h-12 shrink-0 whitespace-nowrap border-y-2 border-t-transparent"
      :class="[
        active === tab.key ? 'tab-active border-b-primary' : 'border-b-transparent',
        { 'flex-1': tab.icon },
      ]"
      :aria-selected="active === tab.key"
      :title="tab.icon && tab.label"
      :to="{ query: { tab: tab.key } }"
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

export default {
  name: 'BaseTabs',
  components: { RouterLink, AppIcon, BaseCard },
  props: {
    tabs: { type: Array, required: true },
    active: { type: String, required: true },
  },
}
</script>

<template>
  <BaseCard role="tablist" class="tabs px-2">
    <RouterLink
      v-for="tab in tabs"
      :key="tab.key"
      role="tab"
      class="tab h-12 border-y-2 border-t-transparent"
      :class="[
        active === tab.key ? 'tab-active border-b-primary' : 'border-b-transparent',
        { 'flex-1': tab.icon },
      ]"
      :aria-selected="active === tab.key"
      :title="tab.icon && tab.label"
      :to="{ query: { tab: tab.key } }"
      replace
    >
      <AppIcon v-if="tab.icon" :name="tab.icon" :alt="tab.label" />
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

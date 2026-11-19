<template>
  <nav
    class="flex shrink-0 [scrollbar-width:none] gap-1 overflow-x-auto border-b border-app-border px-6 py-4 lg:w-64 lg:flex-col lg:overflow-y-auto lg:border-r lg:border-b-0 lg:pr-4"
  >
    <component
      :is="item.href ? 'a' : 'RouterLink'"
      v-for="item in app.navigationItems()"
      :key="item.key"
      v-bind="item.href ? { href: item.href, target: '_blank', rel: 'noopener' } : { to: item.to }"
      class="flex h-10 shrink-0 items-center gap-3 rounded-box px-3 text-sm lg:min-w-0"
      :class="
        activeNavigation === item.key
          ? 'bg-base-200 text-base-content'
          : 'text-app-muted hover:bg-base-200 hover:text-base-content'
      "
    >
      <AppIcon :name="item.icon" />
      <span class="lg:min-w-0 lg:truncate" :title="item.label">{{ item.label }}</span>
    </component>
    <div class="hidden text-xs font-light text-app-muted lg:mt-auto lg:block lg:px-3 lg:pt-6">
      {{ $t('navigation.version', { version: app.version }) }}
    </div>
  </nav>
</template>

<script>
import { RouterLink } from 'vue-router'
import AppIcon from '@core/components/AppIcon.vue'

export default {
  name: 'SideNav',
  components: { RouterLink, AppIcon },
  inject: ['app'],
  props: {
    activeNavigation: { type: String, default: null },
  },
}
</script>

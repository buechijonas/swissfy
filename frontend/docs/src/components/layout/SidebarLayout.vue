<template>
  <div class="flex min-h-[100dvh] flex-col bg-base-100 lg:h-[100dvh] lg:overflow-hidden">
    <TitleHeader :title="app.title" :switches="app.appSwitches" class="mt-5" />
    <div v-if="!isSettings" class="mt-3 border-b border-docs-border"></div>
    <div class="flex flex-1 flex-col lg:min-h-0 lg:flex-row">
      <SideNav v-if="!isSettings" :active-navigation="activeNavigation" />
      <main :key="$route.path" class="flex min-w-0 flex-1 flex-col lg:overflow-y-auto">
        <slot />
      </main>
    </div>
  </div>
</template>

<script>
import SideNav from '@/components/layout/SideNav.vue'
import TitleHeader from '@/components/layout/TitleHeader.vue'

export default {
  name: 'SidebarLayout',
  components: { SideNav, TitleHeader },
  inject: ['app'],
  props: {
    activeNavigation: { type: String, default: null },
  },
  computed: {
    isSettings() {
      return this.$route.name === 'settings'
    },
  },
  watch: {
    '$route.path'() {
      window.scrollTo(0, 0)
    },
  },
}
</script>

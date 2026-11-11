<template>
  <SidebarLayout :active-navigation="$route.meta.activeNavigation">
    <RouterView />
  </SidebarLayout>
</template>

<script>
import { RouterView } from 'vue-router'
import SidebarLayout from '@/components/layout/SidebarLayout.vue'
import { useAuthStore } from '@/stores/auth.js'

export default {
  name: 'App',
  components: { RouterView, SidebarLayout },
  mounted() {
    useAuthStore().fetchMe()
  },
}
</script>

<template>
  <BasePage :active-navigation="$route.meta.activeNavigation">
    <RouterView v-if="authStore.ready" />
  </BasePage>
</template>

<script>
import { RouterView } from 'vue-router'
import BasePage from '@/components/layout/BasePage.vue'
import { useAuthStore } from '@/stores/auth.js'
import { useChatsStore } from '@/stores/chats.js'

const DELIVERY_INTERVAL = 20000

export default {
  name: 'App',
  components: { RouterView, BasePage },
  computed: {
    authStore() {
      return useAuthStore()
    },
  },
  async mounted() {
    await Promise.all([useAuthStore().fetchMe(), this.$router.isReady()])
    const { path, query, hash } = this.$route
    this.$router.replace({ path, query, hash, force: true })
    this.syncChats()
    this.deliveryTimer = setInterval(() => this.syncChats(), DELIVERY_INTERVAL)
    document.addEventListener('visibilitychange', this.syncChats)
  },
  beforeUnmount() {
    clearInterval(this.deliveryTimer)
    document.removeEventListener('visibilitychange', this.syncChats)
  },
  methods: {
    syncChats() {
      if (useAuthStore().isAuthenticated && document.visibilityState === 'visible') {
        useChatsStore()
          .sync()
          .catch(() => {})
      }
    },
  },
}
</script>

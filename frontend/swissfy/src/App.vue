<template>
  <BasePage :active-navigation="$route.meta.activeNavigation">
    <RouterView v-if="authStore.ready" />
  </BasePage>
</template>

<script>
import { mapStores } from 'pinia'
import { RouterView } from 'vue-router'
import { useIntervalFn } from '@vueuse/core'
import BasePage from '@/components/layout/BasePage.vue'
import { documentVisibility } from '@/lib/browser.js'
import { useAuthStore } from '@/stores/auth.js'
import { useChatsStore } from '@/stores/chats.js'
import { useNotificationsStore } from '@/stores/notifications.js'

const DELIVERY_INTERVAL = 20000

export default {
  name: 'App',
  components: { RouterView, BasePage },
  computed: {
    ...mapStores(useAuthStore),
    visible() {
      return documentVisibility.value === 'visible'
    },
  },
  watch: {
    visible() {
      this.syncChats()
    },
  },
  created() {
    this.delivery = useIntervalFn(this.syncChats, DELIVERY_INTERVAL, { immediate: false })
  },
  async mounted() {
    await Promise.all([this.authStore.fetchMe(), this.$router.isReady()])
    const { path, query, hash } = this.$route
    this.$router.replace({ path, query, hash, force: true })
    this.syncChats()
    this.delivery.resume()
  },
  beforeUnmount() {
    this.delivery.pause()
  },
  methods: {
    syncChats() {
      if (!this.visible || !this.authStore.isAuthenticated) return
      useChatsStore()
        .sync()
        .catch(() => {})
      useNotificationsStore()
        .refresh()
        .catch(() => {})
    },
  },
}
</script>

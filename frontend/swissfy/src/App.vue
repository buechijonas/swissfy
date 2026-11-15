<template>
  <BasePage :active-navigation="$route.meta.activeNavigation">
    <RouterView v-if="authStore.ready" />
  </BasePage>
</template>

<script>
import { mapStores } from 'pinia'
import { RouterView } from 'vue-router'
import BasePage from '@/components/layout/BasePage.vue'
import { useAuthStore } from '@/stores/auth.js'
import { useChatsStore } from '@/stores/chats.js'
import { useEventsStore } from '@/stores/events.js'
import { useNotificationsStore } from '@/stores/notifications.js'

export default {
  name: 'App',
  components: { RouterView, BasePage },
  computed: {
    ...mapStores(useAuthStore, useChatsStore, useEventsStore, useNotificationsStore),
  },
  watch: {
    'eventsStore.chat'() {
      this.chatsStore.sync()
    },
    'eventsStore.notification'() {
      this.notificationsStore.refresh()
    },
  },
  async mounted() {
    await Promise.all([this.authStore.fetchMe(), this.$router.isReady()])
    const { path, query, hash } = this.$route
    this.$router.replace({ path, query, hash, force: true })
    if (this.authStore.isAuthenticated) this.eventsStore.connect()
  },
  beforeUnmount() {
    this.eventsStore.disconnect()
  },
}
</script>

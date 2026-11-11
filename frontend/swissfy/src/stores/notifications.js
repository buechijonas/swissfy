import { ref } from 'vue'
import { defineStore } from 'pinia'
import notificationsApi from '@/api/notifications.js'

export const useNotificationsStore = defineStore('notifications', () => {
  const unread = ref(0)

  async function refresh() {
    unread.value = (await notificationsApi.unread()).count
  }

  async function markRead() {
    await notificationsApi.markRead()
    unread.value = 0
  }

  function reset() {
    unread.value = 0
  }

  return { unread, refresh, markRead, reset }
})

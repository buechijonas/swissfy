import { ref } from 'vue'
import { defineStore } from 'pinia'
import { apiFetch } from '@/lib/api.js'

export const useNotificationsStore = defineStore('notifications', () => {
  const unread = ref(0)

  async function refresh() {
    const response = await apiFetch('/api/notifications/unread/')
    if (response.ok) unread.value = (await response.json()).count
  }

  async function markRead() {
    const response = await apiFetch('/api/notifications/read/', { method: 'POST' })
    if (response.ok) unread.value = 0
  }

  function reset() {
    unread.value = 0
  }

  return { unread, refresh, markRead, reset }
})

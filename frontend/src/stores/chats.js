import { ref } from 'vue'
import { defineStore } from 'pinia'
import chatsApi from '@/api/chats.js'

export const useChatsStore = defineStore('chats', () => {
  const unread = ref([])
  const conversations = new Map()

  async function sync() {
    unread.value = (await chatsApi.markDelivered()).unread
  }

  function markRead(username) {
    unread.value = unread.value.filter((name) => name !== username)
  }

  function cachedMessages(username) {
    return conversations.get(username) ?? []
  }

  function cacheMessages(username, messages) {
    conversations.set(username, messages)
  }

  function reset() {
    unread.value = []
    conversations.clear()
  }

  return { unread, sync, markRead, cachedMessages, cacheMessages, reset }
})

import { defineStore } from 'pinia'
import { ref } from 'vue'

const EVENTS_URL = '/api/events/'

export const useEventsStore = defineStore('events', () => {
  const chat = ref(0)
  const notification = ref(0)
  const connected = ref(false)
  let source = null

  function changeChats() {
    chat.value += 1
  }

  function changeNotifications() {
    notification.value += 1
  }

  function sync() {
    connected.value = true
    changeChats()
    changeNotifications()
  }

  function connect() {
    if (source) return
    source = new EventSource(EVENTS_URL)
    source.addEventListener('open', sync)
    source.addEventListener('sync', sync)
    source.addEventListener('chat', changeChats)
    source.addEventListener('notification', changeNotifications)
    source.addEventListener('error', () => {
      connected.value = false
    })
  }

  function disconnect() {
    source?.close()
    source = null
    connected.value = false
  }

  return { chat, notification, connected, connect, disconnect }
})

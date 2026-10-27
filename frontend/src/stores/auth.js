import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { apiFetch, extractErrorMessage } from '@/lib/api.js'
import { clearDeviceToken, readDeviceToken, writeDeviceToken } from '@/lib/deviceToken.js'
import { persistentLogin } from '@/lib/persistentLogin.js'
import { useChatsStore } from '@/stores/chats.js'
import { useNotificationsStore } from '@/stores/notifications.js'
import { useFoldersStore, useGroupsStore } from '@/stores/posts.js'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const ready = ref(false)
  const isAuthenticated = computed(() => user.value !== null)

  async function loadMe() {
    const response = await apiFetch('/api/auth/me/')
    const data = response.ok ? await response.json() : null
    return data?.user ?? null
  }

  async function restoreSession(token) {
    const response = await apiFetch('/api/auth/device/restore/', {
      method: 'POST',
      body: JSON.stringify({ token }),
    })
    if (response.status === 401) await clearDeviceToken()
    const data = response.ok ? await response.json() : null
    return data?.user ?? null
  }

  async function syncDeviceToken(token) {
    const response = await apiFetch('/api/auth/device/', {
      method: 'POST',
      body: JSON.stringify({ token }),
    })
    if (!response.ok) throw new Error('Speichern fehlgeschlagen.')
    await writeDeviceToken((await response.json()).token)
    navigator.storage?.persist?.().catch(() => {})
  }

  async function forgetDevice() {
    const response = await apiFetch('/api/auth/device/', { method: 'DELETE' })
    if (!response.ok) throw new Error('Speichern fehlgeschlagen.')
    await clearDeviceToken()
  }

  async function fetchMe() {
    try {
      const token = persistentLogin.value ? await readDeviceToken() : null
      user.value = (await loadMe()) ?? (token ? await restoreSession(token) : null)
      if (user.value && persistentLogin.value) await syncDeviceToken(token).catch(() => {})
    } finally {
      ready.value = true
    }
  }

  async function setPersistentLogin(enabled) {
    if (enabled) {
      await syncDeviceToken(await readDeviceToken())
    } else {
      await forgetDevice()
    }
    persistentLogin.value = enabled
  }

  function startGovexLogin() {
    window.location.href = '/api/auth/oidc/login/'
  }

  function openGovexAccount() {
    window.location.href = '/api/auth/oidc/account/'
  }

  async function logout() {
    const response = await apiFetch('/api/auth/logout/', { method: 'POST' })
    if (!response.ok) {
      const data = await response.json().catch(() => null)
      throw new Error(extractErrorMessage(data, 'Abmelden fehlgeschlagen.'))
    }
    await clearDeviceToken()
    user.value = null
    useChatsStore().reset()
    useNotificationsStore().reset()
    useFoldersStore().reset()
    useGroupsStore().reset()
  }

  async function acceptConsent(field) {
    const response = await apiFetch(`/api/auth/consent/${field}/`, { method: 'POST' })
    const data = await response.json().catch(() => null)
    if (!response.ok) {
      throw new Error(extractErrorMessage(data, 'Zustimmung fehlgeschlagen.'))
    }
    user.value = { ...user.value, consent: data }
  }

  return {
    user,
    ready,
    isAuthenticated,
    fetchMe,
    startGovexLogin,
    openGovexAccount,
    logout,
    acceptConsent,
    setPersistentLogin,
  }
})

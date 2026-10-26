import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import authApi from '@/api/auth.js'
import { clearDeviceToken, readDeviceToken, writeDeviceToken } from '@/lib/deviceToken.js'
import { persistentLogin } from '@/lib/preferences.js'
import { useChatsStore } from '@/stores/chats.js'
import { useNotificationsStore } from '@/stores/notifications.js'
import { useFoldersStore, useGroupsStore } from '@/stores/posts.js'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const ready = ref(false)
  const isAuthenticated = computed(() => user.value !== null)

  async function loadMe() {
    const data = await authApi.me().catch(() => null)
    return data?.user ?? null
  }

  async function restoreSession(token) {
    try {
      return (await authApi.restoreDevice(token)).user
    } catch (error) {
      if (error.status === 401) await clearDeviceToken()
      return null
    }
  }

  async function syncDeviceToken(token) {
    const data = await authApi.syncDevice(token).catch(() => {
      throw new Error('Speichern fehlgeschlagen.')
    })
    await writeDeviceToken(data.token)
    navigator.storage?.persist?.().catch(() => {})
  }

  async function forgetDevice() {
    await authApi.forgetDevice().catch(() => {
      throw new Error('Speichern fehlgeschlagen.')
    })
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
    window.location.href = authApi.loginUrl()
  }

  function openGovexAccount() {
    window.location.href = authApi.accountUrl()
  }

  async function logout() {
    await authApi.logout().catch((error) => {
      throw new Error(error.detail ?? 'Abmelden fehlgeschlagen.')
    })
    await clearDeviceToken()
    user.value = null
    useChatsStore().reset()
    useNotificationsStore().reset()
    useFoldersStore().reset()
    useGroupsStore().reset()
  }

  async function acceptConsent(field) {
    const consent = await authApi.acceptConsent(field).catch((error) => {
      throw new Error(error.detail ?? 'Zustimmung fehlgeschlagen.')
    })
    user.value = { ...user.value, consent }
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

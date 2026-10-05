import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { apiFetch, extractErrorMessage } from '@/lib/api.js'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const ready = ref(false)
  const isAuthenticated = computed(() => user.value !== null)

  async function fetchMe() {
    try {
      const response = await apiFetch('/api/auth/me/')
      const data = response.ok ? await response.json() : null
      user.value = data?.user ?? null
    } finally {
      ready.value = true
    }
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
    user.value = null
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
  }
})

import { acceptHMRUpdate, defineStore } from 'pinia'
import { ref, computed } from 'vue'
import authApi from '@core/api/auth.js'
import { t } from '@/i18n.js'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const ready = ref(false)
  const isAuthenticated = computed(() => user.value !== null)

  async function fetchMe() {
    try {
      user.value = (await authApi.me().catch(() => null))?.user ?? null
    } finally {
      ready.value = true
    }
  }

  function startGovexLogin() {
    window.location.href = authApi.loginUrl(window.location.origin)
  }

  async function logout() {
    await authApi.logout().catch((error) => {
      throw new Error(error.detail ?? t('auth.logoutFailed'))
    })
    user.value = null
  }

  return { user, ready, isAuthenticated, fetchMe, startGovexLogin, logout }
})

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useAuthStore, import.meta.hot))
}

import { ref, watch } from 'vue'

const STORAGE_KEY = 'persistent-login'

function readStoredValue() {
  try {
    return localStorage.getItem(STORAGE_KEY) !== 'off'
  } catch {
    return true
  }
}

export const persistentLogin = ref(readStoredValue())

watch(persistentLogin, (enabled) => {
  try {
    localStorage.setItem(STORAGE_KEY, enabled ? 'on' : 'off')
  } catch {}
})

import { ref, watch } from 'vue'

const STORAGE_KEY = 'contrast-mode'

function readStoredValue() {
  try {
    return localStorage.getItem(STORAGE_KEY) === 'on'
  } catch {
    return false
  }
}

export const contrastMode = ref(readStoredValue())

function applyContrastMode(enabled) {
  const root = document.documentElement
  if (enabled) {
    root.setAttribute('data-contrast', 'on')
  } else {
    root.removeAttribute('data-contrast')
  }
}

watch(
  contrastMode,
  (enabled) => {
    applyContrastMode(enabled)
    try {
      localStorage.setItem(STORAGE_KEY, enabled ? 'on' : 'off')
    } catch {
      // ignore storage errors (private browsing, disabled storage, etc.)
    }
  },
  { immediate: true },
)

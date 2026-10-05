import { ref, watch } from 'vue'

const STORAGE_KEY = 'dyslexia-font'

function readStoredValue() {
  try {
    return localStorage.getItem(STORAGE_KEY) === 'on'
  } catch {
    return false
  }
}

export const dyslexiaFont = ref(readStoredValue())

function applyDyslexiaFont(enabled) {
  const root = document.documentElement
  if (enabled) {
    root.setAttribute('data-dyslexia', 'on')
  } else {
    root.removeAttribute('data-dyslexia')
  }
}

watch(
  dyslexiaFont,
  (enabled) => {
    applyDyslexiaFont(enabled)
    try {
      localStorage.setItem(STORAGE_KEY, enabled ? 'on' : 'off')
    } catch {
      // ignore storage errors (private browsing, disabled storage, etc.)
    }
  },
  { immediate: true },
)

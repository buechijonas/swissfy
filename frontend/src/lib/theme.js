import { ref, watch } from 'vue'

const STORAGE_KEY = 'theme'
const VALID_MODES = ['auto', 'light', 'dark']

function readStoredMode() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return VALID_MODES.includes(stored) ? stored : 'auto'
  } catch {
    return 'auto'
  }
}

export const themeMode = ref(readStoredMode())

function applyTheme(mode) {
  const root = document.documentElement
  if (mode === 'light') {
    root.setAttribute('data-theme', 'swissfy')
  } else if (mode === 'dark') {
    root.setAttribute('data-theme', 'dark')
  } else {
    root.removeAttribute('data-theme')
  }
}

watch(
  themeMode,
  (mode) => {
    applyTheme(mode)
    try {
      localStorage.setItem(STORAGE_KEY, mode)
    } catch {
      // ignore storage errors (private browsing, disabled storage, etc.)
    }
  },
  { immediate: true },
)

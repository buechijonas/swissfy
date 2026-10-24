import { ref, watch } from 'vue'

const STORAGE_KEY = 'design'
const VALID_DESIGNS = ['default', 'glass', 'cyberpunk']

function readStoredDesign() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return VALID_DESIGNS.includes(stored) ? stored : 'default'
  } catch {
    return 'default'
  }
}

export const design = ref(readStoredDesign())

function applyDesign(value) {
  const root = document.documentElement
  if (value === 'default') {
    root.removeAttribute('data-design')
  } else {
    root.setAttribute('data-design', value)
  }
}

watch(
  design,
  (value) => {
    applyDesign(value)
    try {
      localStorage.setItem(STORAGE_KEY, value)
    } catch {}
  },
  { immediate: true },
)

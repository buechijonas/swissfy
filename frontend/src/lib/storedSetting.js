import { ref, watch } from 'vue'

function readStored(key) {
  try {
    return localStorage.getItem(key)
  } catch {
    return null
  }
}

function writeStored(key, value) {
  try {
    localStorage.setItem(key, value)
  } catch {}
}

function storedRef(key, initial, serialize, apply) {
  const setting = ref(initial)
  watch(
    setting,
    (value) => {
      apply?.(value)
      writeStored(key, serialize(value))
    },
    { immediate: true },
  )
  return setting
}

export function storedChoice(key, choices, apply) {
  const stored = readStored(key)
  return storedRef(key, choices.includes(stored) ? stored : choices[0], String, apply)
}

export function storedFlag(key, { fallback = false, apply } = {}) {
  const stored = readStored(key)
  const initial = stored === null ? fallback : stored === 'on'
  return storedRef(key, initial, (enabled) => (enabled ? 'on' : 'off'), apply)
}

export function rootAttribute(name, value) {
  if (value === null) document.documentElement.removeAttribute(name)
  else document.documentElement.setAttribute(name, value)
}

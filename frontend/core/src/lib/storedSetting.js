import { ref, watch } from 'vue'
import { getCookie, setSharedCookie } from '@core/lib/cookies.js'

const SHARED_MAX_AGE = 60 * 60 * 24 * 400
const sharedSettings = []

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

const localStore = {
  read: readStored,
  write: writeStored,
}

const sharedStore = {
  read: (key) => getCookie(key) ?? readStored(key),
  write: (key, value) => setSharedCookie(key, value, SHARED_MAX_AGE),
}

function storedRef(key, initial, serialize, apply, store) {
  const setting = ref(initial)
  watch(
    setting,
    (value) => {
      apply?.(value)
      store.write(key, serialize(value))
    },
    { immediate: true },
  )
  return setting
}

function parseChoice(choices, stored) {
  return choices.includes(stored) ? stored : choices[0]
}

function parseFlag(fallback, stored) {
  return stored === null ? fallback : stored === 'on'
}

const serializeFlag = (enabled) => (enabled ? 'on' : 'off')

export function storedChoice(key, choices, apply) {
  return storedRef(key, parseChoice(choices, readStored(key)), String, apply, localStore)
}

export function storedFlag(key, { fallback = false, apply } = {}) {
  return storedRef(key, parseFlag(fallback, readStored(key)), serializeFlag, apply, localStore)
}

export function sharedChoice(key, choices, apply) {
  const parse = (stored) => parseChoice(choices, stored)
  const setting = storedRef(key, parse(sharedStore.read(key)), String, apply, sharedStore)
  sharedSettings.push({ key, setting, parse })
  return setting
}

export function sharedFlag(key, { fallback = false, apply } = {}) {
  const parse = (stored) => parseFlag(fallback, stored)
  const setting = storedRef(key, parse(sharedStore.read(key)), serializeFlag, apply, sharedStore)
  sharedSettings.push({ key, setting, parse })
  return setting
}

export function rootAttribute(name, value) {
  if (value === null) document.documentElement.removeAttribute(name)
  else document.documentElement.setAttribute(name, value)
}

document.addEventListener('visibilitychange', () => {
  if (document.visibilityState !== 'visible') return
  sharedSettings.forEach(({ key, setting, parse }) => {
    setting.value = parse(sharedStore.read(key))
  })
})

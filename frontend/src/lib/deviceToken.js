import { deleteCookie, getCookie, setCookie } from '@/lib/cookies.js'
import { keyValueStore } from '@/lib/indexedDb.js'

const KEY = 'swissfy-device'
const COOKIE_MAX_AGE = 60 * 60 * 24 * 400

const cookieBackend = {
  read: () => getCookie(KEY),
  write: (token) => setCookie(KEY, token, COOKIE_MAX_AGE),
  clear: () => deleteCookie(KEY),
}

const localStorageBackend = {
  read: () => localStorage.getItem(KEY),
  write: (token) => localStorage.setItem(KEY, token),
  clear: () => localStorage.removeItem(KEY),
}

const indexedDbStore = keyValueStore('swissfy-auth', 'device')

const indexedDbBackend = {
  read: () => indexedDbStore.get(KEY),
  write: (token) => indexedDbStore.put(KEY, token),
  clear: () => indexedDbStore.delete(KEY),
}

const cacheRequest = `/__${KEY}`

const cacheBackend = {
  async read() {
    const response = await (await caches.open(KEY)).match(cacheRequest)
    return response ? response.text() : null
  },
  async write(token) {
    await (await caches.open(KEY)).put(cacheRequest, new Response(token))
  },
  async clear() {
    await (await caches.open(KEY)).delete(cacheRequest)
  },
}

const backends = [cookieBackend, localStorageBackend, indexedDbBackend, cacheBackend]

function onEveryBackend(method, ...args) {
  return Promise.allSettled(backends.map(async (backend) => backend[method](...args)))
}

export async function readDeviceToken() {
  const results = await onEveryBackend('read')
  const found = results.find((result) => result.status === 'fulfilled' && result.value)
  return found ? found.value : null
}

export async function writeDeviceToken(token) {
  await onEveryBackend('write', token)
}

export async function clearDeviceToken() {
  await onEveryBackend('clear')
}

import { apiFetch, extractErrorMessage } from '@/lib/api.js'
import { generateKeyPair, unwrapWithPin, wrapWithPin } from '@/lib/chatCrypto.js'

const DB_NAME = 'swissfy-chat'
const STORE = 'keys'
const PROTECTION_URL = '/api/chats/protection/'

function openDb() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME)
    request.onupgradeneeded = () => request.result.createObjectStore(STORE)
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error)
  })
}

async function withStore(mode, action) {
  const db = await openDb()
  return new Promise((resolve, reject) => {
    const request = action(db.transaction(STORE, mode).objectStore(STORE))
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error)
  })
}

export async function localKeys(userId) {
  return (await withStore('readonly', (store) => store.get(userId))) ?? []
}

async function addLocalKey(userId, key) {
  const keys = await localKeys(userId)
  await withStore('readwrite', (store) => store.put([...keys, key], userId))
}

async function apiJson(url, options, fallback) {
  const response = await apiFetch(url, options)
  const data = await response.json().catch(() => null)
  if (!response.ok) throw new Error(extractErrorMessage(data, fallback))
  return data
}

export function fetchProtection() {
  return apiJson(PROTECTION_URL, {}, 'Chat-Einstellungen konnten nicht geladen werden.')
}

export async function prepareChatKeys(userId) {
  const protection = await fetchProtection()
  const keys = await localKeys(userId)
  const hasActiveKey = keys.some((key) => protection.keys.some((active) => active.id === key.id))

  if (protection.mode === 'device' && !hasActiveKey) {
    const { publicKey, privateKey } = await generateKeyPair({ extractable: false })
    const key = await apiJson(
      '/api/chats/keys/',
      { method: 'POST', body: JSON.stringify({ public_key: publicKey }) },
      'Schlüssel konnte nicht erstellt werden.',
    )
    await addLocalKey(userId, { id: key.id, ...privateKey })
  }

  const locked = protection.mode === 'pin' && !hasActiveKey
  return { mode: protection.mode, locked, pinKey: protection.pin_key }
}

export async function unlockWithPin(userId, pinKey, pin) {
  let privateKey
  try {
    privateKey = await unwrapWithPin(pinKey, pin)
  } catch {
    throw new Error('Falsche PIN.')
  }
  await addLocalKey(userId, { id: pinKey.id, ...privateKey })
}

export async function setProtection(userId, mode, pin) {
  let privateKey = null
  let key
  if (mode !== 'standard') {
    const pair = await generateKeyPair({ extractable: mode === 'pin' })
    privateKey = pair.privateKey
    key = {
      public_key: pair.publicKey,
      ...(mode === 'pin' ? await wrapWithPin(privateKey, pin) : {}),
    }
  }
  const protection = await apiJson(
    PROTECTION_URL,
    { method: 'PUT', body: JSON.stringify({ mode, ...(key ? { key } : {}) }) },
    'Speichern fehlgeschlagen.',
  )
  if (privateKey) {
    const local = mode === 'pin' ? await unwrapWithPin(protection.pin_key, pin) : privateKey
    await addLocalKey(userId, { id: protection.keys[0].id, ...local })
  }
  return protection
}

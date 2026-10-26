import chatsApi from '@/api/chats.js'
import { generateKeyPair, unwrapWithPin, wrapWithPin } from '@/lib/chatCrypto.js'
import { keyValueStore } from '@/lib/indexedDb.js'

const keyStore = keyValueStore('swissfy-chat', 'keys')

export async function localKeys(userId) {
  return (await keyStore.get(userId)) ?? []
}

async function addLocalKey(userId, key) {
  const keys = await localKeys(userId)
  await keyStore.put(userId, [...keys, key])
}

function failWith(fallback) {
  return (error) => {
    throw new Error(error.detail ?? fallback)
  }
}

export function fetchProtection() {
  return chatsApi.protection().catch(failWith('Chat-Einstellungen konnten nicht geladen werden.'))
}

export async function prepareChatKeys(userId) {
  const protection = await fetchProtection()
  const keys = await localKeys(userId)
  const hasActiveKey = keys.some((key) => protection.keys.some((active) => active.id === key.id))

  if (protection.mode === 'device' && !hasActiveKey) {
    const { publicKey, privateKey } = await generateKeyPair({ extractable: false })
    const key = await chatsApi
      .createKey(publicKey)
      .catch(failWith('Schlüssel konnte nicht erstellt werden.'))
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
  const protection = await chatsApi
    .setProtection({ mode, ...(key ? { key } : {}) })
    .catch(failWith('Speichern fehlgeschlagen.'))
  if (privateKey) {
    const local = mode === 'pin' ? await unwrapWithPin(protection.pin_key, pin) : privateKey
    await addLocalKey(userId, { id: protection.keys[0].id, ...local })
  }
  return protection
}

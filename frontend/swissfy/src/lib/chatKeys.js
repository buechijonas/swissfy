import find from 'lodash-es/find'
import isEqual from 'lodash-es/isEqual'
import map from 'lodash-es/map'
import some from 'lodash-es/some'
import unionBy from 'lodash-es/unionBy'
import chatsApi from '@/api/chats.js'
import { t } from '@/i18n.js'
import {
  generateKeyPair,
  isEndorsed,
  pinSecrets,
  unwrapWithPin,
  wrapWithPin,
} from '@/lib/chatCrypto.js'
import { keyValueStore } from '@/lib/indexedDb.js'

const keyStore = keyValueStore('swissfy-chat', 'keys')
const DAY_MS = 24 * 60 * 60 * 1000
const ROTATION_DAYS = 7

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
  return chatsApi.protection().catch(failWith(t('chatKeys.settingsFailed')))
}

// Private keys the server no longer lists are retired and deleted once the
// server has deleted every message that could have been sealed for them.
export function pruneKeys(keys, activeIds, retentionDays, now) {
  return keys
    .map((key) => (activeIds.includes(key.id) || key.retiredAt ? key : { ...key, retiredAt: now }))
    .filter((key) => !key.retiredAt || now - key.retiredAt <= retentionDays * DAY_MS)
}

export function isRotationDue(serverKey, now) {
  return now - Date.parse(serverKey.created_at) > ROTATION_DAYS * DAY_MS
}

async function retireKeys(userId, protection, now) {
  const keys = await localKeys(userId)
  const pruned = pruneKeys(keys, map(protection.keys, 'id'), protection.retention_days, now)
  if (!isEqual(map(pruned, 'retiredAt'), map(keys, 'retiredAt'))) {
    await keyStore.put(userId, pruned)
  }
  return pruned
}

async function createDeviceKey(userId, keys, replaced, signer = null) {
  const { publicKey, privateKey } = await generateKeyPair({ extractable: false, signer })
  const key = await chatsApi
    .createKey(publicKey, replaced?.id)
    .catch(failWith(t('chatKeys.keyFailed')))
  const now = Date.now()
  const retired = keys.map((local) =>
    local.id === replaced?.id ? { ...local, retiredAt: now } : local,
  )
  await keyStore.put(userId, [...retired, { id: key.id, ...privateKey }])
}

async function renewDeviceKey(userId, keys, activeKey, serverKey, now) {
  if (!activeKey?.sign) return createDeviceKey(userId, keys, activeKey)
  if (!isRotationDue(serverKey, now)) return null
  const signer = { privateKey: activeKey.sign, publicKey: serverKey.public_key.sign }
  return createDeviceKey(userId, keys, activeKey, signer)
}

export async function prepareChatKeys(userId) {
  const protection = await fetchProtection()
  const now = Date.now()
  const keys = await retireKeys(userId, protection, now)
  const activeKey = keys.find((key) => some(protection.keys, { id: key.id }))

  if (protection.mode === 'device') {
    const serverKey = activeKey && find(protection.keys, { id: activeKey.id })
    await renewDeviceKey(userId, keys, activeKey, serverKey, now)
  }

  const locked = protection.mode === 'pin' && !activeKey
  return { mode: protection.mode, locked, pinKey: protection.pin_key }
}

export async function unlockWithPin(userId, pinKey, pin) {
  const { key, verifier } = await pinSecrets(pin, pinKey.salt)
  const sealed = await chatsApi.unlock(verifier).catch(failWith(t('chatKeys.wrongPin')))
  const privateKey = await unwrapWithPin(sealed, key).catch(failWith(t('chatKeys.wrongPin')))
  if (sealed.needs_verifier) {
    await chatsApi.setPinVerifier(verifier).catch(failWith(t('chatKeys.keyFailed')))
  }
  await addLocalKey(userId, { id: pinKey.id, ...privateKey })
}

function saveProtection(body) {
  return chatsApi.setProtection(body).catch(failWith(t('common.saveFailed')))
}

export async function setProtection(userId, mode, pin) {
  if (mode === 'standard') return saveProtection({ mode })
  const pair = await generateKeyPair({ extractable: mode === 'pin' })
  const wrapped = mode === 'pin' ? await wrapWithPin(pair.privateKey, pin) : null
  const protection = await saveProtection({
    mode,
    key: { public_key: pair.publicKey, ...wrapped?.sealed },
  })
  const local = wrapped ? await unwrapWithPin(wrapped.sealed, wrapped.key) : pair.privateKey
  await addLocalKey(userId, { id: protection.keys[0].id, ...local })
  return protection
}

function trustEntry(userId, username) {
  return `${userId}:${username}`
}

export function trustedKeys(userId, username) {
  return keyStore.get(trustEntry(userId, username))
}

export async function trustKeys(userId, username, keys) {
  const known = (await trustedKeys(userId, username)) ?? []
  await keyStore.put(trustEntry(userId, username), unionBy(known, keys, 'id'))
}

// A key is known when it was trusted as it is, or when a trusted identity
// endorsed it, which is how rotated device keys stay trusted.
async function isKnown(trusted, key) {
  if (some(trusted, (known) => known.id === key.id && isEqual(known.public_key, key.public_key))) {
    return true
  }
  const identity = key.public_key.sign
  if (!identity || !some(trusted, (known) => isEqual(known.public_key.sign, identity))) {
    return false
  }
  return isEndorsed(key.public_key)
}

export async function unknownKeys(trusted, keys, owner) {
  const own = keys.filter((key) => key.owner === owner)
  const known = await Promise.all(own.map((key) => isKnown(trusted, key)))
  return own.filter((key, index) => !known[index])
}

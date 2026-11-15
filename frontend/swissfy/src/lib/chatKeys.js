import isEqual from 'lodash-es/isEqual'
import some from 'lodash-es/some'
import unionBy from 'lodash-es/unionBy'
import chatsApi from '@/api/chats.js'
import { generateKeyPair, pinSecrets, unwrapWithPin, wrapWithPin } from '@/lib/chatCrypto.js'
import { keyValueStore } from '@/lib/indexedDb.js'
import { t } from '@/i18n.js'

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
  return chatsApi.protection().catch(failWith(t('chatKeys.settingsFailed')))
}

async function createDeviceKey(userId, replaces) {
  const { publicKey, privateKey } = await generateKeyPair({ extractable: false })
  const key = await chatsApi.createKey(publicKey, replaces).catch(failWith(t('chatKeys.keyFailed')))
  await addLocalKey(userId, { id: key.id, ...privateKey })
}

export async function prepareChatKeys(userId) {
  const protection = await fetchProtection()
  const keys = await localKeys(userId)
  const activeKey = keys.find((key) => some(protection.keys, { id: key.id }))

  if (protection.mode === 'device' && !activeKey?.sign) {
    await createDeviceKey(userId, activeKey?.id)
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

export function unknownKeys(trusted, keys, owner) {
  return keys.filter(
    (key) =>
      key.owner === owner &&
      !some(trusted, (known) => known.id === key.id && isEqual(known.public_key, key.public_key)),
  )
}

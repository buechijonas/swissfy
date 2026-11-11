import { ml_kem768 } from '@noble/post-quantum/ml-kem.js'

const ECDH = { name: 'ECDH', namedCurve: 'P-256' }
const AES = { name: 'AES-GCM', length: 256 }
const HKDF_INFO = new TextEncoder().encode('swissfy-chat-v1')
const PIN_ITERATIONS = 600000

export function toBase64(bytes) {
  let binary = ''
  for (const byte of new Uint8Array(bytes)) binary += String.fromCharCode(byte)
  return btoa(binary)
}

export function fromBase64(text) {
  return Uint8Array.from(atob(text), (c) => c.charCodeAt(0))
}

function randomBytes(length) {
  return crypto.getRandomValues(new Uint8Array(length))
}

async function aesEncrypt(key, plaintext) {
  const iv = randomBytes(12)
  const ciphertext = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, key, plaintext)
  return { ciphertext: toBase64(ciphertext), iv: toBase64(iv) }
}

function aesDecrypt(key, ciphertext, iv) {
  return crypto.subtle.decrypt({ name: 'AES-GCM', iv: fromBase64(iv) }, key, fromBase64(ciphertext))
}

async function hybridKey(kemSecret, ecdhSecret) {
  const material = new Uint8Array([...kemSecret, ...new Uint8Array(ecdhSecret)])
  const hkdfKey = await crypto.subtle.importKey('raw', material, 'HKDF', false, ['deriveKey'])
  return crypto.subtle.deriveKey(
    { name: 'HKDF', hash: 'SHA-256', salt: new Uint8Array(), info: HKDF_INFO },
    hkdfKey,
    AES,
    false,
    ['encrypt', 'decrypt'],
  )
}

export async function generateKeyPair({ extractable }) {
  const ecdh = await crypto.subtle.generateKey(ECDH, extractable, ['deriveBits'])
  const kem = ml_kem768.keygen()
  return {
    publicKey: {
      ecdh: await crypto.subtle.exportKey('jwk', ecdh.publicKey),
      kem: toBase64(kem.publicKey),
    },
    privateKey: { ecdh: ecdh.privateKey, kem: kem.secretKey },
  }
}

async function seal(messageKey, publicKey) {
  const { cipherText, sharedSecret } = ml_kem768.encapsulate(fromBase64(publicKey.kem))
  const ephemeral = await crypto.subtle.generateKey(ECDH, false, ['deriveBits'])
  const recipient = await crypto.subtle.importKey('jwk', publicKey.ecdh, ECDH, false, [])
  const ecdhSecret = await crypto.subtle.deriveBits(
    { name: 'ECDH', public: recipient },
    ephemeral.privateKey,
    256,
  )
  const { ciphertext, iv } = await aesEncrypt(await hybridKey(sharedSecret, ecdhSecret), messageKey)
  return {
    kem: toBase64(cipherText),
    ecdh: await crypto.subtle.exportKey('jwk', ephemeral.publicKey),
    wrapped: ciphertext,
    iv,
  }
}

async function open(envelope, privateKey) {
  const kemSecret = ml_kem768.decapsulate(fromBase64(envelope.kem), privateKey.kem)
  const sender = await crypto.subtle.importKey('jwk', envelope.ecdh, ECDH, false, [])
  const ecdhSecret = await crypto.subtle.deriveBits(
    { name: 'ECDH', public: sender },
    privateKey.ecdh,
    256,
  )
  return aesDecrypt(await hybridKey(kemSecret, ecdhSecret), envelope.wrapped, envelope.iv)
}

export async function encryptMessage(text, keys, withServerKey) {
  const messageKey = randomBytes(32)
  const aesKey = await crypto.subtle.importKey('raw', messageKey, AES, false, ['encrypt'])
  const { ciphertext, iv } = await aesEncrypt(aesKey, new TextEncoder().encode(text))
  const envelopes = await Promise.all(
    keys.map(async (key) => ({ key: key.id, ...(await seal(messageKey, key.public_key)) })),
  )
  return {
    ciphertext,
    iv,
    envelopes,
    ...(withServerKey ? { message_key: toBase64(messageKey) } : {}),
  }
}

export async function decryptMessage(message, localKeys) {
  try {
    let messageKey = message.message_key && fromBase64(message.message_key)
    for (const envelope of message.envelopes) {
      const local = localKeys.find((key) => key.id === envelope.key)
      if (!messageKey && local) messageKey = await open(envelope, local)
    }
    if (!messageKey) return null
    const aesKey = await crypto.subtle.importKey('raw', messageKey, AES, false, ['decrypt'])
    return new TextDecoder().decode(await aesDecrypt(aesKey, message.ciphertext, message.iv))
  } catch {
    return null
  }
}

async function pinKey(pin, salt) {
  const material = await crypto.subtle.importKey(
    'raw',
    new TextEncoder().encode(pin),
    'PBKDF2',
    false,
    ['deriveKey'],
  )
  return crypto.subtle.deriveKey(
    { name: 'PBKDF2', hash: 'SHA-256', salt, iterations: PIN_ITERATIONS },
    material,
    AES,
    false,
    ['encrypt', 'decrypt'],
  )
}

export async function wrapWithPin(privateKey, pin) {
  const salt = randomBytes(16)
  const plaintext = JSON.stringify({
    ecdh: await crypto.subtle.exportKey('jwk', privateKey.ecdh),
    kem: toBase64(privateKey.kem),
  })
  const { ciphertext, iv } = await aesEncrypt(
    await pinKey(pin, salt),
    new TextEncoder().encode(plaintext),
  )
  return { wrapped_private_key: ciphertext, salt: toBase64(salt), iv }
}

export async function unwrapWithPin(pinKeyData, pin) {
  const plaintext = await aesDecrypt(
    await pinKey(pin, fromBase64(pinKeyData.salt)),
    pinKeyData.wrapped_private_key,
    pinKeyData.iv,
  )
  const { ecdh, kem } = JSON.parse(new TextDecoder().decode(plaintext))
  return {
    ecdh: await crypto.subtle.importKey('jwk', ecdh, ECDH, false, ['deriveBits']),
    kem: fromBase64(kem),
  }
}

import { ml_kem768 } from '@noble/post-quantum/ml-kem.js'
import chunk from 'lodash-es/chunk'
import find from 'lodash-es/find'
import some from 'lodash-es/some'

const ECDH = { name: 'ECDH', namedCurve: 'P-256' }
const ECDSA = { name: 'ECDSA', namedCurve: 'P-256' }
const SIGNATURE = { name: 'ECDSA', hash: 'SHA-256' }
const AES = { name: 'AES-GCM', length: 256 }
const HKDF_INFO = new TextEncoder().encode('swissfy-chat-v1')
const SIGNATURE_CONTEXT = 'swissfy-chat-signature-v1'
const PIN_ITERATIONS = 600000
const SAFETY_GROUPS = 12
const SAFETY_GROUP_BYTES = 4

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
  const sign = await crypto.subtle.generateKey(ECDSA, extractable, ['sign', 'verify'])
  const kem = ml_kem768.keygen()
  return {
    publicKey: {
      ecdh: await crypto.subtle.exportKey('jwk', ecdh.publicKey),
      kem: toBase64(kem.publicKey),
      sign: await crypto.subtle.exportKey('jwk', sign.publicKey),
    },
    privateKey: { ecdh: ecdh.privateKey, kem: kem.secretKey, sign: sign.privateKey },
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

function signedContent(recipient, message) {
  const content = [SIGNATURE_CONTEXT, recipient, message.ciphertext, message.iv]
  return new TextEncoder().encode(JSON.stringify(content))
}

async function sign(message, signer) {
  const signature = await crypto.subtle.sign(
    SIGNATURE,
    signer.key.sign,
    signedContent(signer.recipient, message),
  )
  return { ...message, sender_key: signer.key.id, signature: toBase64(signature) }
}

export async function encryptMessage(text, keys, withServerKey, signer = null) {
  const messageKey = randomBytes(32)
  const aesKey = await crypto.subtle.importKey('raw', messageKey, AES, false, ['encrypt'])
  const { ciphertext, iv } = await aesEncrypt(aesKey, new TextEncoder().encode(text))
  const envelopes = await Promise.all(
    keys.map(async (key) => ({ key: key.id, ...(await seal(messageKey, key.public_key)) })),
  )
  const message = {
    ciphertext,
    iv,
    envelopes,
    ...(withServerKey ? { message_key: toBase64(messageKey) } : {}),
  }
  return signer ? sign(message, signer) : message
}

export async function verifyMessage(message, recipient, keys) {
  const signer = find(keys, { id: message.sender_key })
  if (!message.signature || !signer?.public_key.sign) return false
  try {
    const key = await crypto.subtle.importKey('jwk', signer.public_key.sign, ECDSA, false, [
      'verify',
    ])
    const signature = fromBase64(message.signature)
    return await crypto.subtle.verify(SIGNATURE, key, signature, signedContent(recipient, message))
  } catch {
    return false
  }
}

function openMessageKey(message, localKeys) {
  if (message.message_key) return fromBase64(message.message_key)
  const envelope = find(message.envelopes, (candidate) => some(localKeys, { id: candidate.key }))
  return envelope ? open(envelope, find(localKeys, { id: envelope.key })) : null
}

export async function decryptMessage(message, localKeys) {
  try {
    const messageKey = await openMessageKey(message, localKeys)
    if (!messageKey) return { text: null, error: 'missing' }
    const aesKey = await crypto.subtle.importKey('raw', messageKey, AES, false, ['decrypt'])
    const plaintext = await aesDecrypt(aesKey, message.ciphertext, message.iv)
    return { text: new TextDecoder().decode(plaintext), error: null }
  } catch {
    return { text: null, error: 'invalid' }
  }
}

function fingerprint(key) {
  const { ecdh, kem, sign } = key.public_key
  return JSON.stringify([key.owner, ecdh.x, ecdh.y, kem, sign?.x ?? null, sign?.y ?? null])
}

function safetyGroup(bytes) {
  const number = bytes.reduce((value, byte) => value * 256 + byte, 0)
  return String(number % 100000).padStart(5, '0')
}

export async function safetyNumber(keys) {
  const material = new TextEncoder().encode(JSON.stringify(keys.map(fingerprint).sort()))
  const digest = new Uint8Array(await crypto.subtle.digest('SHA-512', material))
  const bytes = Array.from(digest.slice(0, SAFETY_GROUPS * SAFETY_GROUP_BYTES))
  return chunk(bytes, SAFETY_GROUP_BYTES).map(safetyGroup)
}

export async function pinSecrets(pin, salt) {
  const material = await crypto.subtle.importKey(
    'raw',
    new TextEncoder().encode(pin),
    'PBKDF2',
    false,
    ['deriveBits'],
  )
  const bits = await crypto.subtle.deriveBits(
    { name: 'PBKDF2', hash: 'SHA-256', salt: fromBase64(salt), iterations: PIN_ITERATIONS },
    material,
    512,
  )
  const secrets = new Uint8Array(bits)
  return {
    key: await crypto.subtle.importKey('raw', secrets.slice(0, 32), AES, false, [
      'encrypt',
      'decrypt',
    ]),
    verifier: toBase64(secrets.slice(32)),
  }
}

export async function wrapWithPin(privateKey, pin) {
  const salt = toBase64(randomBytes(16))
  const { key, verifier } = await pinSecrets(pin, salt)
  const plaintext = JSON.stringify({
    ecdh: await crypto.subtle.exportKey('jwk', privateKey.ecdh),
    kem: toBase64(privateKey.kem),
    sign: await crypto.subtle.exportKey('jwk', privateKey.sign),
  })
  const { ciphertext, iv } = await aesEncrypt(key, new TextEncoder().encode(plaintext))
  return {
    sealed: { wrapped_private_key: ciphertext, salt, iv, pin_verifier: verifier },
    key,
  }
}

export async function unwrapWithPin(sealed, key) {
  const plaintext = await aesDecrypt(key, sealed.wrapped_private_key, sealed.iv)
  const { ecdh, kem, sign } = JSON.parse(new TextDecoder().decode(plaintext))
  return {
    ecdh: await crypto.subtle.importKey('jwk', ecdh, ECDH, false, ['deriveBits']),
    kem: fromBase64(kem),
    ...(sign ? { sign: await crypto.subtle.importKey('jwk', sign, ECDSA, false, ['sign']) } : {}),
  }
}

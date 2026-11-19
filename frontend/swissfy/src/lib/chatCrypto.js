import { ml_kem768 } from '@noble/post-quantum/ml-kem.js'
import chunk from 'lodash-es/chunk'
import find from 'lodash-es/find'
import some from 'lodash-es/some'
import sortBy from 'lodash-es/sortBy'

const ECDH = { name: 'ECDH', namedCurve: 'P-256' }
const ECDSA = { name: 'ECDSA', namedCurve: 'P-256' }
const SIGNATURE = { name: 'ECDSA', hash: 'SHA-256' }
const AES = { name: 'AES-GCM', length: 256 }
const HKDF_INFO = new TextEncoder().encode('swissfy-chat-v1')
const HKDF_INFO_V2 = new TextEncoder().encode('swissfy-chat-v2')
const MESSAGE_CONTEXT = 'swissfy-chat-message-v2'
const ENVELOPE_CONTEXT = 'swissfy-chat-envelope-v2'
const SIGNATURE_CONTEXT = 'swissfy-chat-signature-v1'
const SIGNATURE_CONTEXT_V2 = 'swissfy-chat-signature-v2'
const ENDORSEMENT_CONTEXT = 'swissfy-chat-endorsement-v1'
export const MESSAGE_VERSION = 2
// A replayed message keeps the send time of its first delivery. Device clocks drift, so only a
// delivery far away from the send time counts as a replay.
const REPLAY_WINDOW_MS = 24 * 60 * 60 * 1000
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

function encode(value) {
  return new TextEncoder().encode(JSON.stringify(value))
}

function gcm(iv, additionalData) {
  return additionalData ? { name: 'AES-GCM', iv, additionalData } : { name: 'AES-GCM', iv }
}

async function aesEncrypt(key, plaintext, additionalData = null) {
  const iv = randomBytes(12)
  const ciphertext = await crypto.subtle.encrypt(gcm(iv, additionalData), key, plaintext)
  return { ciphertext: toBase64(ciphertext), iv: toBase64(iv) }
}

function aesDecrypt(key, ciphertext, iv, additionalData = null) {
  return crypto.subtle.decrypt(gcm(fromBase64(iv), additionalData), key, fromBase64(ciphertext))
}

// From v2 on the binding (KEM ciphertext, ephemeral ECDH key, recipient key) salts the
// derivation, as hybrid combiners like X-Wing do, so no part of an envelope can be swapped alone.
async function hybridKey(kemSecret, ecdhSecret, binding = null) {
  const material = new Uint8Array([...kemSecret, ...new Uint8Array(ecdhSecret)])
  const hkdfKey = await crypto.subtle.importKey('raw', material, 'HKDF', false, ['deriveKey'])
  const salt = binding ? await crypto.subtle.digest('SHA-256', binding) : new Uint8Array()
  const info = binding ? HKDF_INFO_V2 : HKDF_INFO
  return crypto.subtle.deriveKey(
    { name: 'HKDF', hash: 'SHA-256', salt, info },
    hkdfKey,
    AES,
    false,
    ['encrypt', 'decrypt'],
  )
}

async function generateSigner(extractable) {
  const pair = await crypto.subtle.generateKey(ECDSA, extractable, ['sign', 'verify'])
  return { privateKey: pair.privateKey, publicKey: await exportPublic(pair.publicKey) }
}

async function exportPublic(key) {
  const { kty, crv, x, y } = await crypto.subtle.exportKey('jwk', key)
  return { kty, crv, x, y }
}

function endorsedContent({ ecdh, kem }) {
  return new TextEncoder().encode(JSON.stringify([ENDORSEMENT_CONTEXT, ecdh.x, ecdh.y, kem]))
}

async function verifySignature(publicKey, signature, content) {
  try {
    const key = await crypto.subtle.importKey('jwk', publicKey, ECDSA, false, ['verify'])
    return await crypto.subtle.verify(SIGNATURE, key, fromBase64(signature), content)
  } catch {
    return false
  }
}

export function isEndorsed(publicKey) {
  if (!publicKey.endorsement || !publicKey.sign) return Promise.resolve(false)
  return verifySignature(publicKey.sign, publicKey.endorsement, endorsedContent(publicKey))
}

// A signer carries the device identity over from an earlier key, so that only
// the encryption keys rotate and partners keep trusting the device.
export async function generateKeyPair({ extractable, signer = null }) {
  const ecdh = await crypto.subtle.generateKey(ECDH, extractable, ['deriveBits'])
  const identity = signer ?? (await generateSigner(extractable))
  const kem = ml_kem768.keygen()
  const publicKey = {
    ecdh: await exportPublic(ecdh.publicKey),
    kem: toBase64(kem.publicKey),
    sign: identity.publicKey,
  }
  const endorsement = await crypto.subtle.sign(
    SIGNATURE,
    identity.privateKey,
    endorsedContent(publicKey),
  )
  return {
    publicKey: { ...publicKey, endorsement: toBase64(endorsement) },
    privateKey: { ecdh: ecdh.privateKey, kem: kem.secretKey, sign: identity.privateKey },
  }
}

function envelopeBinding(keyId, envelope) {
  return encode([ENVELOPE_CONTEXT, keyId, envelope.kem, envelope.ecdh.x, envelope.ecdh.y])
}

async function seal(messageKey, key) {
  const { cipherText, sharedSecret } = ml_kem768.encapsulate(fromBase64(key.public_key.kem))
  const ephemeral = await crypto.subtle.generateKey(ECDH, false, ['deriveBits'])
  const recipient = await crypto.subtle.importKey('jwk', key.public_key.ecdh, ECDH, false, [])
  const ecdhSecret = await crypto.subtle.deriveBits(
    { name: 'ECDH', public: recipient },
    ephemeral.privateKey,
    256,
  )
  const envelope = { kem: toBase64(cipherText), ecdh: await exportPublic(ephemeral.publicKey) }
  const binding = envelopeBinding(key.id, envelope)
  const wrappingKey = await hybridKey(sharedSecret, ecdhSecret, binding)
  const { ciphertext, iv } = await aesEncrypt(wrappingKey, messageKey, binding)
  return { key: key.id, ...envelope, wrapped: ciphertext, iv }
}

async function open(envelope, privateKey, version) {
  const kemSecret = ml_kem768.decapsulate(fromBase64(envelope.kem), privateKey.kem)
  const sender = await crypto.subtle.importKey('jwk', envelope.ecdh, ECDH, false, [])
  const ecdhSecret = await crypto.subtle.deriveBits(
    { name: 'ECDH', public: sender },
    privateKey.ecdh,
    256,
  )
  const binding = version === MESSAGE_VERSION ? envelopeBinding(envelope.key, envelope) : null
  const wrappingKey = await hybridKey(kemSecret, ecdhSecret, binding)
  return aesDecrypt(wrappingKey, envelope.wrapped, envelope.iv, binding)
}

// Which side of the conversation sent the message. Both names are bound into the message, so a
// server that shows it in another conversation or turns its direction breaks it.
export function conversationOf(message, self, partner) {
  if (message.sender === self) return { sender: self, recipient: partner }
  return { sender: partner, recipient: self }
}

function messageContext({ sender, recipient }) {
  return encode([MESSAGE_CONTEXT, sender, recipient])
}

// v2 signs everything the recipient relies on, envelopes and signing key included, so the server
// can neither strip nor exchange parts of a signed message.
function signedContent(message, { sender, recipient }) {
  if (message.version !== MESSAGE_VERSION) {
    return encode([SIGNATURE_CONTEXT, recipient, message.ciphertext, message.iv])
  }
  const envelopes = sortBy(message.envelopes, 'key').map((envelope) => [
    envelope.key,
    envelope.kem,
    envelope.ecdh.x,
    envelope.ecdh.y,
    envelope.wrapped,
    envelope.iv,
  ])
  return encode([
    SIGNATURE_CONTEXT_V2,
    message.version,
    sender,
    recipient,
    message.sender_key,
    message.ciphertext,
    message.iv,
    envelopes,
  ])
}

export async function encryptMessage(text, keys, { conversation, withServerKey, signer = null }) {
  const messageKey = randomBytes(32)
  const aesKey = await crypto.subtle.importKey('raw', messageKey, AES, false, ['encrypt'])
  const plaintext = encode({ text, sent_at: Date.now(), nonce: toBase64(randomBytes(16)) })
  const { ciphertext, iv } = await aesEncrypt(aesKey, plaintext, messageContext(conversation))
  const message = {
    version: MESSAGE_VERSION,
    ciphertext,
    iv,
    envelopes: await Promise.all(keys.map((key) => seal(messageKey, key))),
    ...(withServerKey ? { message_key: toBase64(messageKey) } : {}),
  }
  if (!signer) return message
  const signed = { ...message, sender_key: signer.id }
  const signature = await crypto.subtle.sign(
    SIGNATURE,
    signer.sign,
    signedContent(signed, conversation),
  )
  return { ...signed, signature: toBase64(signature) }
}

export async function verifyMessage(message, conversation, keys) {
  const signer = find(keys, { id: message.sender_key, owner: conversation.sender })
  if (!message.signature || !signer?.public_key.sign) return false
  return verifySignature(
    signer.public_key.sign,
    message.signature,
    signedContent(message, conversation),
  )
}

// A server could deliver an old signed message a second time. Its send time gives it away, and
// so does its nonce when the conversation already holds it.
export function isReplay(message, earlier) {
  if (!message.nonce) return false
  const drift = Math.abs(Date.parse(message.createdAt) - message.sentAt)
  return drift > REPLAY_WINDOW_MS || some(earlier, { nonce: message.nonce })
}

function openMessageKey(message, localKeys) {
  if (message.message_key) return fromBase64(message.message_key)
  const envelope = find(message.envelopes, (candidate) => some(localKeys, { id: candidate.key }))
  if (!envelope) return null
  return open(envelope, find(localKeys, { id: envelope.key }), message.version)
}

async function readPlaintext(aesKey, message, conversation) {
  if (message.version !== MESSAGE_VERSION) {
    const plaintext = await aesDecrypt(aesKey, message.ciphertext, message.iv)
    return { text: new TextDecoder().decode(plaintext), sentAt: null, nonce: null }
  }
  const context = messageContext(conversation)
  const plaintext = await aesDecrypt(aesKey, message.ciphertext, message.iv, context)
  const { text, sent_at, nonce } = JSON.parse(new TextDecoder().decode(plaintext))
  return { text, sentAt: sent_at, nonce }
}

export async function decryptMessage(message, localKeys, conversation) {
  try {
    const messageKey = await openMessageKey(message, localKeys)
    if (!messageKey) return { text: null, sentAt: null, nonce: null, error: 'missing' }
    const aesKey = await crypto.subtle.importKey('raw', messageKey, AES, false, ['decrypt'])
    return { ...(await readPlaintext(aesKey, message, conversation)), error: null }
  } catch {
    return { text: null, sentAt: null, nonce: null, error: 'invalid' }
  }
}

// Keys with a signing identity are fingerprinted by it alone, so rotating the
// encryption keys keeps the safety number. Older keys without one fall back to
// their encryption keys.
function fingerprint(key) {
  const { ecdh, kem, sign } = key.public_key
  return JSON.stringify(sign ? [key.owner, sign.x, sign.y] : [key.owner, ecdh.x, ecdh.y, kem])
}

function safetyGroup(bytes) {
  const number = bytes.reduce((value, byte) => value * 256 + byte, 0)
  return String(number % 100000).padStart(5, '0')
}

export async function safetyNumber(keys) {
  const material = new TextEncoder().encode(JSON.stringify(keys.map(fingerprint).toSorted()))
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

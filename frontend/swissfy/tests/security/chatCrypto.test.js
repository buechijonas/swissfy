import { ml_kem768 } from '@noble/post-quantum/ml-kem.js'
import { describe, expect, it } from 'vitest'
import {
  decryptMessage,
  encryptMessage,
  isReplay,
  fromBase64,
  generateKeyPair,
  isEndorsed,
  pinSecrets,
  safetyNumber,
  toBase64,
  unwrapWithPin,
  verifyMessage,
  wrapWithPin,
} from '@/lib/chatCrypto.js'

async function keyWithId(id, owner = 'alice') {
  const pair = await generateKeyPair({ extractable: true })
  return { id, owner, public_key: pair.publicKey, privateKey: pair.privateKey }
}

function flip(base64) {
  const bytes = fromBase64(base64)
  bytes[0] ^= 1
  return toBase64(bytes)
}

const CONVERSATION = { sender: 'alice', recipient: 'bob' }

function encrypt(text, keys, options = {}) {
  return encryptMessage(text, keys, {
    conversation: CONVERSATION,
    withServerKey: false,
    ...options,
  })
}

async function textOf(message, key, conversation = CONVERSATION) {
  return (await decryptMessage(message, [{ id: key.id, ...key.privateKey }], conversation)).text
}

function signedBy(key) {
  return encrypt('geheim', [key], { signer: { id: key.id, ...key.privateKey } })
}

async function legacyWrap(privateKey, pin) {
  const salt = crypto.getRandomValues(new Uint8Array(16))
  const material = await crypto.subtle.importKey(
    'raw',
    new TextEncoder().encode(pin),
    'PBKDF2',
    false,
    ['deriveKey'],
  )
  const key = await crypto.subtle.deriveKey(
    { name: 'PBKDF2', hash: 'SHA-256', salt, iterations: 600000 },
    material,
    { name: 'AES-GCM', length: 256 },
    false,
    ['encrypt'],
  )
  const iv = crypto.getRandomValues(new Uint8Array(12))
  const plaintext = JSON.stringify({
    ecdh: await crypto.subtle.exportKey('jwk', privateKey.ecdh),
    kem: toBase64(privateKey.kem),
  })
  const ciphertext = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv },
    key,
    new TextEncoder().encode(plaintext),
  )
  return { wrapped_private_key: toBase64(ciphertext), salt: toBase64(salt), iv: toBase64(iv) }
}

// The v1 format as clients sent it before v2, to prove old messages stay readable.
async function legacyEncrypt(text, key, signer = null) {
  const messageKey = crypto.getRandomValues(new Uint8Array(32))
  const { cipherText, sharedSecret } = ml_kem768.encapsulate(fromBase64(key.public_key.kem))
  const ecdh = { name: 'ECDH', namedCurve: 'P-256' }
  const ephemeral = await crypto.subtle.generateKey(ecdh, true, ['deriveBits'])
  const recipient = await crypto.subtle.importKey('jwk', key.public_key.ecdh, ecdh, false, [])
  const ecdhSecret = await crypto.subtle.deriveBits(
    { name: 'ECDH', public: recipient },
    ephemeral.privateKey,
    256,
  )
  const material = new Uint8Array([...sharedSecret, ...new Uint8Array(ecdhSecret)])
  const hkdf = await crypto.subtle.importKey('raw', material, 'HKDF', false, ['deriveKey'])
  const info = new TextEncoder().encode('swissfy-chat-v1')
  const aes = { name: 'AES-GCM', length: 256 }
  const params = { name: 'HKDF', hash: 'SHA-256', salt: new Uint8Array(), info }
  const wrappingKey = await crypto.subtle.deriveKey(params, hkdf, aes, false, ['encrypt'])
  const seal = async (cryptoKey, plaintext) => {
    const iv = crypto.getRandomValues(new Uint8Array(12))
    const ciphertext = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, cryptoKey, plaintext)
    return { ciphertext: toBase64(ciphertext), iv: toBase64(iv) }
  }
  const wrapped = await seal(wrappingKey, messageKey)
  const bodyKey = await crypto.subtle.importKey('raw', messageKey, aes, false, ['encrypt'])
  const body = await seal(bodyKey, new TextEncoder().encode(text))
  const message = {
    ciphertext: body.ciphertext,
    iv: body.iv,
    envelopes: [
      {
        key: key.id,
        kem: toBase64(cipherText),
        ecdh: await crypto.subtle.exportKey('jwk', ephemeral.publicKey),
        wrapped: wrapped.ciphertext,
        iv: wrapped.iv,
      },
    ],
  }
  if (!signer) return message
  const content = ['swissfy-chat-signature-v1', 'bob', message.ciphertext, message.iv]
  const signature = await crypto.subtle.sign(
    { name: 'ECDSA', hash: 'SHA-256' },
    signer.sign,
    new TextEncoder().encode(JSON.stringify(content)),
  )
  return { ...message, sender_key: signer.id, signature: toBase64(signature) }
}

describe('chat encryption', () => {
  it('lets only the addressed key decrypt', async () => {
    const alice = await keyWithId(1)
    const eve = await keyWithId(2)
    const message = await encrypt('geheim', [alice])

    expect(await textOf(message, alice)).toBe('geheim')
    expect(await textOf(message, eve)).toBeNull()
    expect(await textOf(message, { ...eve, id: 1 })).toBeNull()
  })

  it('reports a message without a key for this device as missing', async () => {
    const alice = await keyWithId(1)
    const eve = await keyWithId(2)
    const message = await encrypt('geheim', [alice])
    const result = await decryptMessage(message, [{ id: 2, ...eve.privateKey }], CONVERSATION)
    expect(result).toEqual({ text: null, sentAt: null, nonce: null, error: 'missing' })
  })

  it('reports a message that fails to decrypt as invalid', async () => {
    const alice = await keyWithId(1)
    const message = await encrypt('geheim', [alice])
    message.ciphertext = flip(message.ciphertext)
    const result = await decryptMessage(message, [{ id: 1, ...alice.privateKey }], CONVERSATION)
    expect(result).toEqual({ text: null, sentAt: null, nonce: null, error: 'invalid' })
  })

  it('does not send the message key unless asked to', async () => {
    const alice = await keyWithId(1)
    expect(await encrypt('x', [alice])).not.toHaveProperty('message_key')
    expect(await encrypt('x', [alice], { withServerKey: true })).toHaveProperty('message_key')
  })

  it.each(['ciphertext', 'iv'])('rejects a tampered %s', async (field) => {
    const alice = await keyWithId(1)
    const message = await encrypt('geheim', [alice])
    message[field] = flip(message[field])
    expect(await textOf(message, alice)).toBeNull()
  })

  it.each(['kem', 'wrapped', 'iv'])('rejects a tampered envelope %s', async (field) => {
    const alice = await keyWithId(1)
    const message = await encrypt('geheim', [alice])
    message.envelopes[0][field] = flip(message.envelopes[0][field])
    expect(await textOf(message, alice)).toBeNull()
  })

  it('rejects a swapped ephemeral key', async () => {
    const alice = await keyWithId(1)
    const message = await encrypt('geheim', [alice])
    const other = await encrypt('anders', [alice])
    message.envelopes[0].ecdh = other.envelopes[0].ecdh
    expect(await textOf(message, alice)).toBeNull()
  })

  it('uses a fresh key and iv for every message', async () => {
    const alice = await keyWithId(1)
    const first = await encrypt('gleich', [alice], { withServerKey: true })
    const second = await encrypt('gleich', [alice], { withServerKey: true })
    expect(first.ciphertext).not.toBe(second.ciphertext)
    expect(first.iv).not.toBe(second.iv)
    expect(first.message_key).not.toBe(second.message_key)
  })

  it('reports garbage as invalid instead of throwing', async () => {
    const garbage = { ciphertext: '!!', iv: '', envelopes: [{ key: 1 }] }
    expect(await decryptMessage(garbage, [{ id: 1 }], CONVERSATION)).toMatchObject({
      text: null,
      error: 'invalid',
    })
  })
})

describe('message signatures', () => {
  it('names the signing key', async () => {
    const alice = await keyWithId(1)
    const message = await signedBy(alice)
    expect(message.sender_key).toBe(1)
    expect(message.signature).toBeTruthy()
  })

  it('verifies a signed message', async () => {
    const alice = await keyWithId(1)
    expect(await verifyMessage(await signedBy(alice), CONVERSATION, [alice])).toBe(true)
  })

  it('rejects an unsigned message', async () => {
    const alice = await keyWithId(1)
    const message = await encrypt('geheim', [alice])
    expect(await verifyMessage(message, CONVERSATION, [alice])).toBe(false)
  })

  it('rejects a message signed by an unknown key', async () => {
    const alice = await keyWithId(1)
    const mallory = await keyWithId(1, 'mallory')
    expect(await verifyMessage(await signedBy(mallory), CONVERSATION, [alice])).toBe(false)
  })

  it('rejects a message with a replaced ciphertext', async () => {
    const alice = await keyWithId(1)
    const message = await signedBy(alice)
    message.ciphertext = flip(message.ciphertext)
    expect(await verifyMessage(message, CONVERSATION, [alice])).toBe(false)
  })

  it('rejects a message forwarded to another recipient', async () => {
    const alice = await keyWithId(1)
    expect(
      await verifyMessage(await signedBy(alice), { ...CONVERSATION, recipient: 'eve' }, [alice]),
    ).toBe(false)
  })

  it('rejects a garbage signature', async () => {
    const alice = await keyWithId(1)
    const message = { ...(await signedBy(alice)), signature: '!!' }
    expect(await verifyMessage(message, CONVERSATION, [alice])).toBe(false)
  })
})

describe('message format v2', () => {
  it('marks its version and carries send time and nonce inside the ciphertext', async () => {
    const alice = await keyWithId(1)
    const before = Date.now()
    const message = await encrypt('geheim', [alice])
    const result = await decryptMessage(message, [{ id: 1, ...alice.privateKey }], CONVERSATION)
    expect(message.version).toBe(2)
    expect(result.text).toBe('geheim')
    expect(result.sentAt).toBeGreaterThanOrEqual(before)
    expect(fromBase64(result.nonce)).toHaveLength(16)
  })

  it.each([
    ['another recipient', { sender: 'alice', recipient: 'eve' }],
    ['the other direction', { sender: 'bob', recipient: 'alice' }],
  ])('cannot be read as a message to %s', async (_, conversation) => {
    const alice = await keyWithId(1)
    const message = await encrypt('geheim', [alice])
    expect(await textOf(message, alice, conversation)).toBeNull()
  })

  it('binds every envelope to its key', async () => {
    const alice = await keyWithId(1)
    const message = await encrypt('geheim', [alice])
    message.envelopes[0].key = 2
    expect(await textOf(message, { ...alice, id: 2 })).toBeNull()
  })

  it('keeps reading v1 messages', async () => {
    const alice = await keyWithId(1)
    const message = await legacyEncrypt('alt', alice)
    const result = await decryptMessage(message, [{ id: 1, ...alice.privateKey }], CONVERSATION)
    expect(result).toEqual({ text: 'alt', sentAt: null, nonce: null, error: null })
  })

  it('keeps verifying signed v1 messages', async () => {
    const alice = await keyWithId(1)
    const message = await legacyEncrypt('alt', alice, { id: 1, ...alice.privateKey })
    expect(await verifyMessage(message, CONVERSATION, [alice])).toBe(true)
  })

  it('cannot be downgraded to v1', async () => {
    const alice = await keyWithId(1)
    const message = { ...(await signedBy(alice)), version: undefined }
    expect(await textOf(message, alice)).toBeNull()
    expect(await verifyMessage(message, CONVERSATION, [alice])).toBe(false)
  })
})

describe('v2 signatures', () => {
  it.each([
    ['a stripped envelope', (message) => ({ ...message, envelopes: [] })],
    ['another signing key', (message) => ({ ...message, sender_key: 2 })],
  ])('reject %s', async (_, tamper) => {
    const alice = await keyWithId(1)
    const other = { ...(await keyWithId(2)), public_key: alice.public_key }
    const message = tamper(await signedBy(alice))
    expect(await verifyMessage(message, CONVERSATION, [alice, other])).toBe(false)
  })

  it('reject a key of the recipient as signer', async () => {
    const bob = await keyWithId(1, 'bob')
    expect(await verifyMessage(await signedBy(bob), CONVERSATION, [bob])).toBe(false)
  })
})

describe('replays', () => {
  const message = { nonce: 'bm9uY2U=', sentAt: Date.parse('2026-11-18T10:00:00Z') }

  it('accept a delivery close to the send time', () => {
    expect(isReplay({ ...message, createdAt: '2026-11-18T10:05:00Z' }, [])).toBe(false)
  })

  it('catch a delivery long after the send time', () => {
    expect(isReplay({ ...message, createdAt: '2026-11-20T10:00:00Z' }, [])).toBe(true)
  })

  it('catch a nonce the conversation already holds', () => {
    const fresh = { ...message, createdAt: '2026-11-18T10:05:00Z' }
    expect(isReplay(fresh, [{ nonce: message.nonce }])).toBe(true)
  })

  it('leave v1 messages without a nonce alone', () => {
    expect(isReplay({ nonce: null, sentAt: null, createdAt: '2026-11-18T10:00:00Z' }, [])).toBe(
      false,
    )
  })
})

describe('safety numbers', () => {
  it('are the same for both sides', async () => {
    const alice = await keyWithId(1, 'alice')
    const bob = await keyWithId(2, 'bob')
    expect(await safetyNumber([alice, bob])).toEqual(await safetyNumber([bob, alice]))
  })

  it('consist of twelve groups of five digits', async () => {
    const groups = await safetyNumber([await keyWithId(1)])
    expect(groups).toHaveLength(12)
    expect(groups.every((group) => /^\d{5}$/.test(group))).toBe(true)
  })

  it('stay the same when a device rotates its encryption keys', async () => {
    const alice = await keyWithId(1, 'alice')
    const signer = { privateKey: alice.privateKey.sign, publicKey: alice.public_key.sign }
    const rotated = await generateKeyPair({ extractable: true, signer })
    const next = { id: 3, owner: 'alice', public_key: rotated.publicKey }
    expect(rotated.publicKey.ecdh).not.toEqual(alice.public_key.ecdh)
    expect(await safetyNumber([next])).toEqual(await safetyNumber([alice]))
  })

  it('change when a key is replaced', async () => {
    const alice = await keyWithId(1, 'alice')
    const bob = await keyWithId(2, 'bob')
    const mallory = await keyWithId(2, 'bob')
    expect(await safetyNumber([alice, bob])).not.toEqual(await safetyNumber([alice, mallory]))
  })
})

describe('PIN-wrapped keys', () => {
  it('opens with the right PIN only', async () => {
    const pair = await generateKeyPair({ extractable: true })
    const { sealed } = await wrapWithPin(pair.privateKey, '123456')
    const right = await pinSecrets('123456', sealed.salt)
    const wrong = await pinSecrets('654321', sealed.salt)
    await expect(unwrapWithPin(sealed, right.key)).resolves.toHaveProperty('sign')
    await expect(unwrapWithPin(sealed, wrong.key)).rejects.toThrow()
  })

  it('derives the verifier sent to the server from the PIN', async () => {
    const pair = await generateKeyPair({ extractable: true })
    const { sealed } = await wrapWithPin(pair.privateKey, '123456')
    expect((await pinSecrets('123456', sealed.salt)).verifier).toBe(sealed.pin_verifier)
    expect((await pinSecrets('654321', sealed.salt)).verifier).not.toBe(sealed.pin_verifier)
  })

  it('never sends the PIN or the wrapping key as verifier', async () => {
    const pair = await generateKeyPair({ extractable: true })
    const { sealed } = await wrapWithPin(pair.privateKey, '123456')
    expect(fromBase64(sealed.pin_verifier)).toHaveLength(32)
    expect(sealed.pin_verifier).not.toContain('123456')
  })

  it('still opens keys wrapped before verifiers existed', async () => {
    const pair = await generateKeyPair({ extractable: true })
    const sealed = await legacyWrap(pair.privateKey, '123456')
    const { key } = await pinSecrets('123456', sealed.salt)
    const opened = await unwrapWithPin(sealed, key)
    expect(opened).toHaveProperty('kem')
    expect(opened).not.toHaveProperty('sign')
  })

  it('uses a random salt per wrap', async () => {
    const pair = await generateKeyPair({ extractable: true })
    const first = (await wrapWithPin(pair.privateKey, '123456')).sealed
    const second = (await wrapWithPin(pair.privateKey, '123456')).sealed
    expect(first.salt).not.toBe(second.salt)
    expect(first.wrapped_private_key).not.toBe(second.wrapped_private_key)
    expect(first.pin_verifier).not.toBe(second.pin_verifier)
  })
})

describe('key endorsements', () => {
  it('are made by the identity of the device', async () => {
    const { publicKey } = await generateKeyPair({ extractable: false })
    expect(await isEndorsed(publicKey)).toBe(true)
  })

  it('carry the identity over to a rotated key', async () => {
    const first = await generateKeyPair({ extractable: false })
    const signer = { privateKey: first.privateKey.sign, publicKey: first.publicKey.sign }
    const rotated = await generateKeyPair({ extractable: false, signer })
    expect(rotated.publicKey.sign).toEqual(first.publicKey.sign)
    expect(rotated.privateKey.sign).toBe(first.privateKey.sign)
    expect(await isEndorsed(rotated.publicKey)).toBe(true)
  })

  it('reject swapped encryption keys', async () => {
    const own = await generateKeyPair({ extractable: false })
    const foreign = await generateKeyPair({ extractable: false })
    expect(await isEndorsed({ ...own.publicKey, kem: foreign.publicKey.kem })).toBe(false)
    expect(await isEndorsed({ ...own.publicKey, ecdh: foreign.publicKey.ecdh })).toBe(false)
  })

  it('reject an endorsement by another identity', async () => {
    const own = await generateKeyPair({ extractable: false })
    const foreign = await generateKeyPair({ extractable: false })
    expect(await isEndorsed({ ...own.publicKey, sign: foreign.publicKey.sign })).toBe(false)
  })

  it('reject keys without or with a broken endorsement', async () => {
    const { publicKey } = await generateKeyPair({ extractable: false })
    expect(await isEndorsed({ ...publicKey, endorsement: undefined })).toBe(false)
    expect(await isEndorsed({ ...publicKey, endorsement: flip(publicKey.endorsement) })).toBe(false)
    expect(await isEndorsed({ ...publicKey, endorsement: 'kaputt' })).toBe(false)
  })

  it('still lets a rotated key decrypt what was sealed for it', async () => {
    const first = await keyWithId(1)
    const signer = { privateKey: first.privateKey.sign, publicKey: first.public_key.sign }
    const pair = await generateKeyPair({ extractable: true, signer })
    const rotated = {
      id: 2,
      owner: 'alice',
      public_key: pair.publicKey,
      privateKey: pair.privateKey,
    }
    const message = await encrypt('geheim', [rotated])
    expect(await textOf(message, rotated)).toBe('geheim')
    expect(await textOf(message, first)).toBeNull()
  })
})

import { describe, expect, it } from 'vitest'
import {
  decryptMessage,
  encryptMessage,
  fromBase64,
  generateKeyPair,
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

async function textOf(message, key) {
  return (await decryptMessage(message, [{ id: key.id, ...key.privateKey }])).text
}

async function signedBy(key, recipient = 'bob') {
  const signer = { key: { id: key.id, ...key.privateKey }, recipient }
  return encryptMessage('geheim', [key], false, signer)
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

describe('chat encryption', () => {
  it('lets only the addressed key decrypt', async () => {
    const alice = await keyWithId(1)
    const eve = await keyWithId(2)
    const message = await encryptMessage('geheim', [alice], false)

    expect(await textOf(message, alice)).toBe('geheim')
    expect(await textOf(message, eve)).toBeNull()
    expect(await textOf(message, { ...eve, id: 1 })).toBeNull()
  })

  it('reports a message without a key for this device as missing', async () => {
    const alice = await keyWithId(1)
    const eve = await keyWithId(2)
    const message = await encryptMessage('geheim', [alice], false)
    const result = await decryptMessage(message, [{ id: 2, ...eve.privateKey }])
    expect(result).toEqual({ text: null, error: 'missing' })
  })

  it('reports a message that fails to decrypt as invalid', async () => {
    const alice = await keyWithId(1)
    const message = await encryptMessage('geheim', [alice], false)
    message.ciphertext = flip(message.ciphertext)
    const result = await decryptMessage(message, [{ id: 1, ...alice.privateKey }])
    expect(result).toEqual({ text: null, error: 'invalid' })
  })

  it('does not send the message key unless asked to', async () => {
    const alice = await keyWithId(1)
    expect(await encryptMessage('x', [alice], false)).not.toHaveProperty('message_key')
    expect(await encryptMessage('x', [alice], true)).toHaveProperty('message_key')
  })

  it.each(['ciphertext', 'iv'])('rejects a tampered %s', async (field) => {
    const alice = await keyWithId(1)
    const message = await encryptMessage('geheim', [alice], false)
    message[field] = flip(message[field])
    expect(await textOf(message, alice)).toBeNull()
  })

  it.each(['kem', 'wrapped', 'iv'])('rejects a tampered envelope %s', async (field) => {
    const alice = await keyWithId(1)
    const message = await encryptMessage('geheim', [alice], false)
    message.envelopes[0][field] = flip(message.envelopes[0][field])
    expect(await textOf(message, alice)).toBeNull()
  })

  it('rejects a swapped ephemeral key', async () => {
    const alice = await keyWithId(1)
    const message = await encryptMessage('geheim', [alice], false)
    const other = await encryptMessage('anders', [alice], false)
    message.envelopes[0].ecdh = other.envelopes[0].ecdh
    expect(await textOf(message, alice)).toBeNull()
  })

  it('uses a fresh key and iv for every message', async () => {
    const alice = await keyWithId(1)
    const first = await encryptMessage('gleich', [alice], true)
    const second = await encryptMessage('gleich', [alice], true)
    expect(first.ciphertext).not.toBe(second.ciphertext)
    expect(first.iv).not.toBe(second.iv)
    expect(first.message_key).not.toBe(second.message_key)
  })

  it('reports garbage as invalid instead of throwing', async () => {
    const garbage = { ciphertext: '!!', iv: '', envelopes: [{ key: 1 }] }
    expect(await decryptMessage(garbage, [{ id: 1 }])).toEqual({ text: null, error: 'invalid' })
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
    expect(await verifyMessage(await signedBy(alice), 'bob', [alice])).toBe(true)
  })

  it('rejects an unsigned message', async () => {
    const alice = await keyWithId(1)
    const message = await encryptMessage('geheim', [alice], false)
    expect(await verifyMessage(message, 'bob', [alice])).toBe(false)
  })

  it('rejects a message signed by an unknown key', async () => {
    const alice = await keyWithId(1)
    const mallory = await keyWithId(1, 'mallory')
    expect(await verifyMessage(await signedBy(mallory), 'bob', [alice])).toBe(false)
  })

  it('rejects a message with a replaced ciphertext', async () => {
    const alice = await keyWithId(1)
    const message = await signedBy(alice)
    message.ciphertext = flip(message.ciphertext)
    expect(await verifyMessage(message, 'bob', [alice])).toBe(false)
  })

  it('rejects a message forwarded to another recipient', async () => {
    const alice = await keyWithId(1)
    expect(await verifyMessage(await signedBy(alice, 'bob'), 'eve', [alice])).toBe(false)
  })

  it('rejects a garbage signature', async () => {
    const alice = await keyWithId(1)
    const message = { ...(await signedBy(alice)), signature: '!!' }
    expect(await verifyMessage(message, 'bob', [alice])).toBe(false)
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

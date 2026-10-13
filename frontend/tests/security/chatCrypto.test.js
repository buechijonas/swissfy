// @vitest-environment node
import { describe, expect, it } from 'vitest'
import {
  decryptMessage,
  encryptMessage,
  fromBase64,
  generateKeyPair,
  toBase64,
  unwrapWithPin,
  wrapWithPin,
} from '@/lib/chatCrypto.js'

async function keyWithId(id) {
  const pair = await generateKeyPair({ extractable: true })
  return { id, public_key: pair.publicKey, privateKey: pair.privateKey }
}

function flip(base64) {
  const bytes = fromBase64(base64)
  bytes[0] ^= 1
  return toBase64(bytes)
}

describe('chat encryption', () => {
  it('lets only the addressed key decrypt', async () => {
    const alice = await keyWithId(1)
    const eve = await keyWithId(2)
    const message = await encryptMessage('geheim', [alice], false)

    expect(await decryptMessage(message, [{ id: 1, ...alice.privateKey }])).toBe('geheim')
    expect(await decryptMessage(message, [{ id: 2, ...eve.privateKey }])).toBeNull()
    expect(await decryptMessage(message, [{ id: 1, ...eve.privateKey }])).toBeNull()
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
    expect(await decryptMessage(message, [{ id: 1, ...alice.privateKey }])).toBeNull()
  })

  it.each(['kem', 'wrapped', 'iv'])('rejects a tampered envelope %s', async (field) => {
    const alice = await keyWithId(1)
    const message = await encryptMessage('geheim', [alice], false)
    message.envelopes[0][field] = flip(message.envelopes[0][field])
    expect(await decryptMessage(message, [{ id: 1, ...alice.privateKey }])).toBeNull()
  })

  it('rejects a swapped ephemeral key', async () => {
    const alice = await keyWithId(1)
    const message = await encryptMessage('geheim', [alice], false)
    const other = await encryptMessage('anders', [alice], false)
    message.envelopes[0].ecdh = other.envelopes[0].ecdh
    expect(await decryptMessage(message, [{ id: 1, ...alice.privateKey }])).toBeNull()
  })

  it('uses a fresh key and iv for every message', async () => {
    const alice = await keyWithId(1)
    const first = await encryptMessage('gleich', [alice], true)
    const second = await encryptMessage('gleich', [alice], true)
    expect(first.ciphertext).not.toBe(second.ciphertext)
    expect(first.iv).not.toBe(second.iv)
    expect(first.message_key).not.toBe(second.message_key)
  })

  it('returns null for garbage instead of throwing', async () => {
    const garbage = { ciphertext: '!!', iv: '', envelopes: [{ key: 1 }] }
    expect(await decryptMessage(garbage, [{ id: 1 }])).toBeNull()
  })
})

describe('PIN-wrapped keys', () => {
  it('opens with the right PIN only', async () => {
    const pair = await generateKeyPair({ extractable: true })
    const wrapped = await wrapWithPin(pair.privateKey, '123456')
    await expect(unwrapWithPin(wrapped, '123456')).resolves.toHaveProperty('kem')
    await expect(unwrapWithPin(wrapped, '654321')).rejects.toThrow()
  })

  it('uses a random salt per wrap', async () => {
    const pair = await generateKeyPair({ extractable: true })
    const first = await wrapWithPin(pair.privateKey, '123456')
    const second = await wrapWithPin(pair.privateKey, '123456')
    expect(first.salt).not.toBe(second.salt)
    expect(first.wrapped_private_key).not.toBe(second.wrapped_private_key)
  })
})

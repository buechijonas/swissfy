import { beforeEach, describe, expect, it, vi } from 'vitest'
import chatsApi from '@/api/chats.js'
import { generateKeyPair, isEndorsed } from '@/lib/chatCrypto.js'
import {
  isRotationDue,
  localKeys,
  prepareChatKeys,
  pruneKeys,
  unknownKeys,
} from '@/lib/chatKeys.js'

const stored = vi.hoisted(() => new Map())

vi.mock('@/lib/indexedDb.js', () => ({
  keyValueStore: () => ({
    get: (key) => Promise.resolve(stored.get(key)),
    put: (key, value) => Promise.resolve(stored.set(key, value)),
  }),
}))
vi.mock('@/api/chats.js', () => ({ default: { protection: vi.fn(), createKey: vi.fn() } }))

const DAY = 24 * 60 * 60 * 1000
const NOW = Date.parse('2026-11-18T12:00:00Z')

function daysAgo(days) {
  return new Date(NOW - days * DAY).toISOString()
}

async function deviceKey(id, owner = 'anna', signer = null) {
  const pair = await generateKeyPair({ extractable: false, signer })
  return { id, owner, public_key: pair.publicKey, privateKey: pair.privateKey }
}

function signerOf(key) {
  return { privateKey: key.privateKey.sign, publicKey: key.public_key.sign }
}

describe('pruning local keys', () => {
  it('keeps the keys the server still lists', () => {
    expect(pruneKeys([{ id: 1 }], [1], 14, NOW)).toEqual([{ id: 1 }])
  })

  it('retires keys the server no longer lists', () => {
    expect(pruneKeys([{ id: 1 }], [], 14, NOW)).toEqual([{ id: 1, retiredAt: NOW }])
  })

  it('keeps a retired key as long as messages for it may still exist', () => {
    const key = { id: 1, retiredAt: NOW - 14 * DAY }
    expect(pruneKeys([key], [], 14, NOW)).toEqual([key])
  })

  it('deletes a retired key once those messages are gone', () => {
    expect(pruneKeys([{ id: 1, retiredAt: NOW - 14 * DAY - 1 }], [], 14, NOW)).toEqual([])
  })
})

describe('rotation schedule', () => {
  it.each([
    [6, false],
    [7, false],
    [8, true],
  ])('rotates a key created %i days ago: %s', (days, due) => {
    expect(isRotationDue({ created_at: daysAgo(days) }, NOW)).toBe(due)
  })
})

describe('trusting partner keys', () => {
  it('trusts a rotated key endorsed by a trusted identity', async () => {
    const first = await deviceKey(1)
    const rotated = await deviceKey(2, 'anna', signerOf(first))
    expect(await unknownKeys([first], [rotated], 'anna')).toEqual([])
  })

  it('warns about a key of a new identity', async () => {
    const first = await deviceKey(1)
    const stranger = await deviceKey(2)
    expect(await unknownKeys([first], [stranger], 'anna')).toEqual([stranger])
  })

  it('warns about a trusted identity whose endorsement was forged', async () => {
    const first = await deviceKey(1)
    const other = await deviceKey(2)
    const forged = { ...other, public_key: { ...other.public_key, sign: first.public_key.sign } }
    expect(await unknownKeys([first], [forged], 'anna')).toEqual([forged])
  })

  it('does not treat two keys without identity as the same device', async () => {
    const legacy = { id: 1, owner: 'anna', public_key: { kem: 'YQ==' } }
    const other = { id: 2, owner: 'anna', public_key: { kem: 'Yg==' } }
    expect(await unknownKeys([legacy], [other], 'anna')).toEqual([other])
  })

  it('only checks the keys of the partner', async () => {
    const own = await deviceKey(1, 'jonas')
    expect(await unknownKeys([], [own], 'anna')).toEqual([])
  })
})

describe('preparing device keys', () => {
  beforeEach(() => {
    stored.clear()
    vi.clearAllMocks()
    vi.useFakeTimers({ now: NOW, toFake: ['Date'] })
    chatsApi.createKey.mockImplementation((publicKey) =>
      Promise.resolve({ id: 9, public_key: publicKey }),
    )
  })

  async function setUp(createdDaysAgo) {
    const current = await deviceKey(1)
    stored.set(7, [{ id: 1, ...current.privateKey }])
    chatsApi.protection.mockResolvedValue({
      mode: 'device',
      retention_days: 14,
      keys: [{ id: 1, created_at: daysAgo(createdDaysAgo), public_key: current.public_key }],
    })
    return current
  }

  it('keeps a fresh key', async () => {
    await setUp(3)
    await prepareChatKeys(7)
    expect(chatsApi.createKey).not.toHaveBeenCalled()
  })

  it('rotates a due key under the same identity and retires the old one', async () => {
    const current = await setUp(8)
    await prepareChatKeys(7)

    const [publicKey, replaces] = chatsApi.createKey.mock.calls[0]
    expect(replaces).toBe(1)
    expect(publicKey.sign).toEqual(current.public_key.sign)
    expect(publicKey.ecdh).not.toEqual(current.public_key.ecdh)
    expect(await isEndorsed(publicKey)).toBe(true)

    const [old, next] = await localKeys(7)
    expect(old).toMatchObject({ id: 1, retiredAt: NOW })
    expect(next.id).toBe(9)
    expect(next.sign).toBe(old.sign)
  })

  it('deletes the private keys of retired keys after the retention', async () => {
    await setUp(3)
    stored.get(7).push({ id: 2, retiredAt: NOW - 15 * DAY }, { id: 3, retiredAt: NOW - DAY })
    await prepareChatKeys(7)
    expect(stored.get(7).map((key) => key.id)).toEqual([1, 3])
  })
})

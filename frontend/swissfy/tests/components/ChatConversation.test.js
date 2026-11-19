import { flushPromises, mount, RouterLinkStub } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import chatsApi from '@/api/chats.js'
import profilesApi from '@/api/profiles.js'
import ChatConversation from '@/components/chats/ChatConversation.vue'
import { decryptMessage, encryptMessage, verifyMessage } from '@/lib/chatCrypto.js'
import { localKeys, prepareChatKeys, trustedKeys, trustKeys } from '@/lib/chatKeys.js'
import { useAuthStore } from '@/stores/auth.js'
import { useEventsStore } from '@/stores/events.js'

vi.mock('@/api/chats.js', () => ({
  default: { keys: vi.fn(), receive: vi.fn(), send: vi.fn() },
}))
vi.mock('@/api/profiles.js', () => ({ default: { get: vi.fn() } }))
vi.mock('@/lib/chatKeys.js', async (importOriginal) => ({
  unknownKeys: (await importOriginal()).unknownKeys,
  localKeys: vi.fn(),
  prepareChatKeys: vi.fn(),
  trustedKeys: vi.fn(),
  trustKeys: vi.fn(),
  unlockWithPin: vi.fn(),
}))
vi.mock('@/lib/chatCrypto.js', async (importOriginal) => ({
  conversationOf: (await importOriginal()).conversationOf,
  isReplay: (await importOriginal()).isReplay,
  decryptMessage: vi.fn((encrypted) => Promise.resolve({ text: encrypted.text, error: null })),
  encryptMessage: vi.fn(),
  isEndorsed: vi.fn(() => Promise.resolve(false)),
  safetyNumber: vi.fn(() => Promise.resolve(['12345', '67890'])),
  verifyMessage: vi.fn(() => Promise.resolve(true)),
}))

const ANNA_KEY = { id: 7, owner: 'anna', public_key: { kem: 'a2Vt' } }
const OWN_KEY = { id: 3, owner: 'jonas', public_key: { kem: 'b3du' } }

function page(messages, chatRequest = { status: 'accepted', incoming: false }) {
  return { messages, statuses: {}, chat_request: chatRequest, can_request: true }
}

function message(id, text) {
  return {
    id,
    text,
    sender: 'anna',
    is_own: false,
    status: null,
    created_at: '2026-11-14T10:00:00Z',
  }
}

async function mountConversation() {
  const wrapper = mount(ChatConversation, {
    props: { username: 'anna' },
    global: { stubs: { RouterLink: RouterLinkStub } },
  })
  await flushPromises()
  return wrapper
}

describe('ChatConversation', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    useAuthStore().user = { id: 1, username: 'jonas' }
    vi.clearAllMocks()
    localKeys.mockResolvedValue([])
    trustedKeys.mockResolvedValue(undefined)
    profilesApi.get.mockResolvedValue({ username: 'anna', can_view: true, is_self: false })
    prepareChatKeys.mockResolvedValue({ locked: false, pinKey: null })
    chatsApi.keys.mockResolvedValue({ keys: [], server_key: true, retention_days: 14 })
    chatsApi.receive.mockResolvedValue(page([message(1, 'Hoi')]))
  })

  it('shows the messages once it is ready', async () => {
    const wrapper = await mountConversation()
    expect(wrapper.vm.phase).toBe('ready')
    expect(wrapper.text()).toContain('Hoi')
    expect(wrapper.text()).toContain('nach 14 Tagen')
  })

  it('refreshes when the server reports a chat change', async () => {
    const wrapper = await mountConversation()
    chatsApi.receive.mockResolvedValue(page([message(2, 'Grüezi')]))
    useEventsStore().chat += 1
    await flushPromises()
    expect(chatsApi.receive).toHaveBeenLastCalledWith('anna', true, 1)
    expect(wrapper.text()).toContain('Grüezi')
  })

  it('catches up on chat changes that arrive during a refresh', async () => {
    const wrapper = await mountConversation()
    const pending = Promise.withResolvers()
    chatsApi.receive.mockReturnValueOnce(pending.promise)
    useEventsStore().chat += 1
    await flushPromises()
    useEventsStore().chat += 1
    await flushPromises()
    expect(chatsApi.receive).toHaveBeenCalledTimes(2)

    chatsApi.receive.mockResolvedValue(page([message(3, 'Spät')]))
    pending.resolve(page([message(2, 'Grüezi')]))
    await flushPromises()
    expect(chatsApi.receive).toHaveBeenCalledTimes(3)
    expect(chatsApi.receive).toHaveBeenLastCalledWith('anna', true, 2)
    expect(wrapper.text()).toContain('Spät')
  })

  it('shows a failed refresh and clears it after the next one', async () => {
    const wrapper = await mountConversation()
    chatsApi.receive.mockRejectedValue(new Error('offline'))
    useEventsStore().chat += 1
    await flushPromises()
    expect(wrapper.text()).toContain('Chat konnte nicht aktualisiert werden.')

    chatsApi.receive.mockResolvedValue(page([]))
    useEventsStore().chat += 1
    await flushPromises()
    expect(wrapper.text()).not.toContain('Chat konnte nicht aktualisiert werden.')
  })

  it('refuses a chat with yourself', async () => {
    profilesApi.get.mockResolvedValue({ username: 'anna', can_view: true, is_self: true })
    const wrapper = await mountConversation()
    expect(wrapper.vm.phase).toBe('failed')
    expect(wrapper.text()).toContain('Mit dir selbst kannst du nicht chatten.')
  })

  it('asks for the PIN when the keys are locked', async () => {
    prepareChatKeys.mockResolvedValue({ locked: true, pinKey: { id: 3 } })
    const wrapper = await mountConversation()
    expect(wrapper.vm.phase).toBe('locked')
    expect(wrapper.find('input[type="password"]').exists()).toBe(true)
    expect(chatsApi.receive).not.toHaveBeenCalled()
  })

  it('offers the request answers for an incoming request', async () => {
    chatsApi.receive.mockResolvedValue(page([], { status: 'pending', incoming: true }))
    const wrapper = await mountConversation()
    expect(wrapper.text()).toContain('Annehmen')
    expect(wrapper.find('textarea').exists()).toBe(false)
  })

  describe('end-to-end chats', () => {
    beforeEach(() => {
      chatsApi.keys.mockResolvedValue({
        keys: [OWN_KEY, ANNA_KEY],
        server_key: false,
        retention_days: 14,
      })
    })

    it('trusts the keys of a first conversation', async () => {
      await mountConversation()
      expect(trustKeys).toHaveBeenCalledWith(1, 'anna', [OWN_KEY, ANNA_KEY])
    })

    it('warns when the partner has a key that was not trusted before', async () => {
      trustedKeys.mockResolvedValue([OWN_KEY])
      const wrapper = await mountConversation()
      expect(wrapper.text()).toContain('@anna hat neue Schlüssel.')
      expect(wrapper.text()).toContain('12345 67890')
    })

    it('stays quiet when the partner keys are known', async () => {
      trustedKeys.mockResolvedValue([OWN_KEY, ANNA_KEY])
      const wrapper = await mountConversation()
      expect(wrapper.text()).not.toContain('neue Schlüssel')
    })

    it('trusts the new keys once the warning is accepted', async () => {
      trustedKeys.mockResolvedValue([OWN_KEY])
      const wrapper = await mountConversation()
      await wrapper.find('.btn-primary').trigger('click')
      await flushPromises()
      expect(trustKeys).toHaveBeenLastCalledWith(1, 'anna', [OWN_KEY, ANNA_KEY])
      expect(wrapper.text()).not.toContain('neue Schlüssel')
    })

    it('blocks writing until new partner keys are confirmed', async () => {
      trustedKeys.mockResolvedValue([OWN_KEY])
      const wrapper = await mountConversation()
      const composer = wrapper.find('textarea')
      expect(composer.attributes('disabled')).toBeDefined()
      expect(composer.attributes('placeholder')).toBe('Bestätige zuerst die neuen Schlüssel')

      await wrapper.find('.btn-primary').trigger('click')
      await flushPromises()
      expect(wrapper.find('textarea').attributes('disabled')).toBeUndefined()
    })

    it('does not resend to keys that changed while sending', async () => {
      trustedKeys.mockResolvedValue([OWN_KEY, ANNA_KEY])
      encryptMessage.mockResolvedValue({})
      chatsApi.send.mockRejectedValue({ status: 409 })
      const wrapper = await mountConversation()
      const newKey = { ...ANNA_KEY, id: 8 }
      chatsApi.keys.mockResolvedValue({
        keys: [OWN_KEY, newKey],
        server_key: false,
        retention_days: 14,
      })
      await expect(wrapper.vm.deliver('Hoi')).rejects.toMatchObject({
        status: 409,
        detail: 'Bestätige zuerst die neuen Schlüssel',
      })
      expect(chatsApi.send).toHaveBeenCalledTimes(1)
    })

    it('marks a replayed message as unverified', async () => {
      const replayed = { text: 'alt', error: null, sentAt: Date.parse('2026-11-01'), nonce: 'bg==' }
      decryptMessage.mockResolvedValueOnce(replayed)
      const wrapper = await mountConversation()
      expect(wrapper.text()).toContain('Nicht verifiziert')
    })

    it('marks incoming messages without a valid signature', async () => {
      verifyMessage.mockResolvedValue(false)
      const wrapper = await mountConversation()
      expect(wrapper.text()).toContain('Nicht verifiziert')
    })

    it('verifies incoming messages as sent from the partner to this user', async () => {
      await mountConversation()
      const conversation = { sender: 'anna', recipient: 'jonas' }
      expect(verifyMessage).toHaveBeenCalledWith(expect.objectContaining({ id: 1 }), conversation, [
        OWN_KEY,
        ANNA_KEY,
      ])
    })

    it('signs with the active key of this device', async () => {
      const signingKey = { id: 3, sign: 'private' }
      localKeys.mockResolvedValue([{ id: 2, sign: 'old' }, signingKey])
      encryptMessage.mockResolvedValue({})
      chatsApi.send.mockResolvedValue({ retry_after: 0 })
      const wrapper = await mountConversation()
      await wrapper.vm.deliver('Hoi')
      expect(encryptMessage).toHaveBeenCalledWith('Hoi', [OWN_KEY, ANNA_KEY], {
        conversation: { sender: 'jonas', recipient: 'anna' },
        withServerKey: false,
        signer: signingKey,
      })
    })
  })

  it('does not mark messages in chats the server can read', async () => {
    verifyMessage.mockResolvedValue(false)
    const wrapper = await mountConversation()
    expect(wrapper.text()).not.toContain('Nicht verifiziert')
  })
})

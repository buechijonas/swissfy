import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import ChatComposer from '@/components/chats/ChatComposer.vue'
import { t } from '@/i18n.js'

function mountComposer(deliver, blockedReason = null) {
  return mount(ChatComposer, { props: { deliver, blockedReason } })
}

async function send(wrapper, text = 'Hoi') {
  await wrapper.find('textarea').setValue(text)
  await wrapper.find('form').trigger('submit')
  await flushPromises()
}

function sendButton(wrapper) {
  return wrapper.find('button[type="submit"]')
}

describe('ChatComposer', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('delivers the trimmed draft and clears it', async () => {
    const deliver = vi.fn(() => Promise.resolve({ retry_after: 0 }))
    const wrapper = mountComposer(deliver)
    await send(wrapper, '  Hoi  ')
    expect(deliver).toHaveBeenCalledWith('Hoi')
    expect(wrapper.find('textarea').element.value).toBe('')
  })

  it('does not deliver blank drafts', async () => {
    const deliver = vi.fn()
    await send(mountComposer(deliver), '   ')
    expect(deliver).not.toHaveBeenCalled()
  })

  it('does not deliver while the chat is blocked', async () => {
    const deliver = vi.fn()
    const wrapper = mountComposer(deliver, 'Gesperrt')
    expect(wrapper.find('textarea').attributes('placeholder')).toBe('Gesperrt')
    await send(wrapper)
    expect(deliver).not.toHaveBeenCalled()
  })

  it('counts the slow mode down before the next message', async () => {
    const wrapper = mountComposer(vi.fn(() => Promise.resolve({ retry_after: 2 })))
    await send(wrapper)
    expect(sendButton(wrapper).text()).toBe('2 s')
    await wrapper.find('textarea').setValue('Nochmal')
    expect(sendButton(wrapper).attributes('disabled')).toBeDefined()

    await vi.advanceTimersByTimeAsync(2000)
    expect(sendButton(wrapper).attributes('disabled')).toBeUndefined()
  })

  it('keeps the draft and shows the error when delivery fails', async () => {
    const wrapper = mountComposer(vi.fn(() => Promise.reject({ status: 403, detail: 'Nein' })))
    await send(wrapper)
    expect(wrapper.find('textarea').element.value).toBe('Hoi')
    expect(wrapper.text()).toContain('Nein')
  })

  it('falls back to a generic error without a detail', async () => {
    const wrapper = mountComposer(vi.fn(() => Promise.reject({ status: 500 })))
    await send(wrapper)
    expect(wrapper.text()).toContain(t('chat.sendFailed'))
  })

  it('only starts the cooldown when rate limited', async () => {
    const limited = { status: 429, detail: 'Zu schnell', data: { retry_after: 3 } }
    const wrapper = mountComposer(vi.fn(() => Promise.reject(limited)))
    await send(wrapper)
    expect(sendButton(wrapper).text()).toBe('3 s')
    expect(wrapper.text()).not.toContain('Zu schnell')
  })
})

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import StoryViewer from '@/components/posts/StoryViewer.vue'

function story(id, overrides = {}) {
  return {
    id,
    image: `/api/stories/${id}/image/`,
    text: '',
    created_at: new Date().toISOString(),
    is_own: false,
    liked: false,
    like_count: null,
    view_count: null,
    seen: false,
    ...overrides,
  }
}

async function mountViewer(stories) {
  const wrapper = mount(StoryViewer, {
    props: { stories, author: { username: 'anna' } },
    global: { stubs: { teleport: true }, mocks: { $route: { path: '/profile/anna' } } },
  })
  wrapper.vm.open()
  await wrapper.vm.$nextTick()
  return wrapper
}

function calls(method) {
  return fetch.mock.calls
    .filter(([, options]) => (options?.method ?? 'GET') === method)
    .map(([url]) => url)
}

describe('StoryViewer', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.stubGlobal(
      'fetch',
      vi.fn((url) =>
        Promise.resolve(
          new Response(JSON.stringify(story(url.split('/')[3], { liked: true })), { status: 200 }),
        ),
      ),
    )
    HTMLDialogElement.prototype.showModal = vi.fn()
    HTMLDialogElement.prototype.close = vi.fn()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
  })

  it('starts at the first unseen story and reports only unseen views', async () => {
    const wrapper = await mountViewer([story('a', { seen: true }), story('b'), story('c')])
    await flushPromises()
    expect(wrapper.find('img[alt="Story"]').attributes('src')).toBe('/api/stories/b/image/')
    expect(calls('POST')).toEqual(['/api/stories/b/view/'])
  })

  it('advances automatically and closes after the last story', async () => {
    const wrapper = await mountViewer([story('a'), story('b')])
    await vi.advanceTimersByTimeAsync(5000)
    expect(wrapper.find('img[alt="Story"]').attributes('src')).toBe('/api/stories/b/image/')
    await vi.advanceTimersByTimeAsync(5000)
    expect(wrapper.find('img[alt="Story"]').exists()).toBe(false)
    await flushPromises()
    expect(wrapper.emitted('closed')).toHaveLength(1)
  })

  it('goes to the next story on a single tap', async () => {
    const wrapper = await mountViewer([story('a'), story('b')])
    await wrapper.find('[role="dialog"]').trigger('click')
    await vi.advanceTimersByTimeAsync(260)
    expect(wrapper.find('img[alt="Story"]').attributes('src')).toBe('/api/stories/b/image/')
  })

  it('likes on a double tap without skipping', async () => {
    const wrapper = await mountViewer([story('a'), story('b')])
    const overlay = wrapper.find('[role="dialog"]')
    await overlay.trigger('click')
    await overlay.trigger('click')
    await vi.advanceTimersByTimeAsync(300)
    expect(wrapper.find('img[alt="Story"]').attributes('src')).toBe('/api/stories/a/image/')
    expect(calls('POST')).toContain('/api/stories/a/like/')
  })

  it('does not like twice on a double tap of a liked story', async () => {
    const wrapper = await mountViewer([story('a', { liked: true })])
    const overlay = wrapper.find('[role="dialog"]')
    await overlay.trigger('click')
    await overlay.trigger('click')
    expect(calls('POST').filter((url) => url.endsWith('/like/'))).toHaveLength(0)
  })

  it.each([
    [true, true],
    [false, false],
  ])('owner controls are shown only to the owner (own=%s)', async (isOwn, visible) => {
    const wrapper = await mountViewer([
      story('a', { is_own: isOwn, view_count: '3', like_count: '1' }),
    ])
    expect(wrapper.find('button[title="Mehr"]').exists()).toBe(visible)
    expect(wrapper.find('button[title="Gesehen von"]').exists()).toBe(visible)
  })

  it('pauses while the owner menu is open', async () => {
    const wrapper = await mountViewer([story('a', { is_own: true }), story('b', { is_own: true })])
    await wrapper.find('button[title="Mehr"]').trigger('click')
    await vi.advanceTimersByTimeAsync(10000)
    expect(wrapper.find('img[alt="Story"]').attributes('src')).toBe('/api/stories/a/image/')
  })

  it('closes on escape', async () => {
    const wrapper = await mountViewer([story('a')])
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    await wrapper.vm.$nextTick()
    expect(wrapper.find('img[alt="Story"]').exists()).toBe(false)
  })

  it('renders story text as plain text', async () => {
    const wrapper = await mountViewer([story('a', { text: '<img src=x onerror=alert(1)>' })])
    expect(wrapper.findAll('img')).toHaveLength(2)
    expect(wrapper.text()).toContain('<img src=x onerror=alert(1)>')
  })
})

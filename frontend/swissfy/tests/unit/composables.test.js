import { mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { effectScope } from 'vue'
import { useAsyncAction } from '@core/composables/asyncAction.js'
import { useClock } from '@/composables/clock.js'
import { useDoubleTap } from '@/composables/doubleTap.js'
import { usePostFeed } from '@/composables/postFeed.js'

function inScope(create) {
  const scope = effectScope()
  return { value: scope.run(create), scope }
}

function page(results, next = null) {
  return new Response(JSON.stringify({ results, next }), { status: 200 })
}

describe('useAsyncAction', () => {
  it('is busy while the task runs and returns its result', async () => {
    const action = useAsyncAction()
    const running = action.run(() => Promise.resolve('ok'))
    expect(action.busy).toBe(true)
    expect(await running).toBe('ok')
    expect(action.busy).toBe(false)
  })

  it.each([
    [{ detail: 'Nein' }, 'Fallback', 'Nein'],
    [{ message: 'kaputt' }, 'Fallback', 'Fallback'],
    [{ message: 'kaputt' }, null, 'kaputt'],
  ])('reports %o with fallback %j as %j', async (failure, fallback, expected) => {
    const action = useAsyncAction()
    expect(await action.run(() => Promise.reject(failure), fallback)).toBeNull()
    expect(action.error).toBe(expected)
  })

  it('clears the previous error when it runs again', async () => {
    const action = useAsyncAction()
    await action.run(() => Promise.reject({ detail: 'Nein' }))
    await action.run(() => Promise.resolve())
    expect(action.error).toBeNull()
  })
})

describe('useDoubleTap', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('runs the single action once the double tap window passed', () => {
    const { value: taps, scope } = inScope(useDoubleTap)
    const single = vi.fn()
    taps.tap(single, vi.fn())
    expect(taps.pending).toBe(true)
    vi.advanceTimersByTime(250)
    expect(single).toHaveBeenCalledOnce()
    expect(taps.pending).toBe(false)
    scope.stop()
  })

  it('runs only the double action for two quick taps', () => {
    const { value: taps, scope } = inScope(useDoubleTap)
    const single = vi.fn()
    const double = vi.fn()
    taps.tap(single, double)
    taps.tap(single, double)
    vi.advanceTimersByTime(250)
    expect(double).toHaveBeenCalledOnce()
    expect(single).not.toHaveBeenCalled()
    scope.stop()
  })

  it('accepts taps without a single action', () => {
    const { value: taps, scope } = inScope(useDoubleTap)
    taps.tap(null, vi.fn())
    expect(() => vi.advanceTimersByTime(250)).not.toThrow()
    scope.stop()
  })
})

describe('useClock', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('stops with the component that creates it in data()', () => {
    const wrapper = mount({
      data() {
        return { clock: useClock() }
      },
      template: '<span>{{ clock.now }}</span>',
    })
    const start = wrapper.vm.clock.now
    wrapper.unmount()
    vi.advanceTimersByTime(30000)
    expect(wrapper.vm.clock.now).toBe(start)
  })

  it('moves on every 30 seconds and on demand', () => {
    const { value: clock, scope } = inScope(useClock)
    const start = clock.now
    vi.advanceTimersByTime(30000)
    expect(clock.now).toBe(start + 30000)
    vi.setSystemTime(start + 31000)
    clock.tick()
    expect(clock.now).toBe(start + 31000)
    scope.stop()
  })
})

describe('usePostFeed', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('loads page after page until there is no next page', async () => {
    fetch
      .mockResolvedValueOnce(page([{ id: 1 }], 'http://swissfy.test/api/posts/?cursor=2'))
      .mockResolvedValueOnce(page([{ id: 2 }]))
    const feed = usePostFeed({ url: () => '/api/posts/', loadError: () => 'Fehler' })
    await feed.loadMore()
    await feed.loadMore()
    await feed.loadMore()
    expect(fetch).toHaveBeenCalledTimes(2)
    expect(feed.posts).toEqual([{ id: 1 }, { id: 2 }])
    expect(feed.hasMore).toBe(false)
  })

  it('skips posts it already shows', async () => {
    fetch.mockResolvedValueOnce(page([{ id: 1 }, { id: 2 }]))
    const feed = usePostFeed({
      url: () => '/api/posts/',
      loadError: () => '',
      initial: [{ id: 1 }],
    })
    await feed.loadMore()
    expect(feed.posts).toEqual([{ id: 1 }, { id: 2 }])
  })

  it('stops loading after an error', async () => {
    fetch.mockResolvedValueOnce(new Response('{}', { status: 500 }))
    const feed = usePostFeed({ url: () => '/api/posts/', loadError: () => 'Fehler' })
    await feed.loadMore()
    await feed.loadMore()
    expect(feed.error).toBe('Fehler')
    expect(fetch).toHaveBeenCalledOnce()
  })

  it('replaces and removes posts by their key', () => {
    const key = (item) => `${item.type}-${item.id}`
    const initial = [
      { type: 'post', id: 1, text: 'alt' },
      { type: 'comment', id: 1 },
    ]
    const feed = usePostFeed({ url: () => null, loadError: () => '', initial, key })
    feed.replace({ type: 'post', id: 1, text: 'neu' })
    expect(feed.posts[0].text).toBe('neu')
    feed.remove({ type: 'comment' })
    expect(feed.posts).toHaveLength(1)
    expect(feed.hasMore).toBe(false)
  })
})

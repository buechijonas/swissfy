import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import BubbleNavigation from '@/components/common/BubbleNavigation.vue'
import { dragBubble, keyAt, stretchFor } from '@/lib/bubble.js'
import { design } from '@/lib/preferences.js'

const BOXES = { home: { left: 0, width: 50 }, reels: { left: 50, width: 50 } }

async function mountNavigation(props = {}) {
  let nav = null
  const wrapper = mount(BubbleNavigation, {
    props: { active: 'home', trackWidth: 100, ...props },
    slots: {
      default: (slot) => {
        nav = slot
        return null
      },
    },
  })
  for (const [key, box] of Object.entries(BOXES)) nav.storeBox(key, box)
  await flushPromises()
  return { wrapper, nav: () => nav }
}

describe('bubble geometry', () => {
  it.each([
    [10, 'home'],
    [75, 'reels'],
    [120, undefined],
  ])('finds the item at %i: %s', (x, key) => {
    expect(keyAt(BOXES, x)).toBe(key)
  })

  it('keeps the dragged bubble inside the track', () => {
    expect(dragBubble(5, 40, 100)).toEqual({ left: 0, width: 40 })
    expect(dragBubble(98, 40, 100)).toEqual({ left: 60, width: 40 })
  })

  it('stretches with the speed up to a limit', () => {
    expect(stretchFor(0)).toBe(1)
    expect(stretchFor(10)).toBe(1.45)
  })
})

describe('BubbleNavigation', () => {
  let previous

  beforeEach(() => {
    previous = design.value
    design.value = 'glass'
  })

  afterEach(() => {
    design.value = previous
  })

  it('sits on the active item', async () => {
    const { nav } = await mountNavigation()
    expect(nav().bubble).toEqual(BOXES.home)
  })

  it('can only be grabbed in the glass design', async () => {
    design.value = 'classic'
    const { nav } = await mountNavigation()
    expect(nav().handlers.grab(10)).toBe(false)
  })

  it('can only be grabbed on the active item when asked to', async () => {
    const { nav } = await mountNavigation({ grabActiveOnly: true })
    expect(nav().handlers.grab(75)).toBe(false)
    expect(nav().handlers.grab(10)).toBe(true)
  })

  it('selects the item it is released on', async () => {
    const { wrapper, nav } = await mountNavigation()
    nav().handlers.grab(10)
    nav().handlers.move(70, 0)
    nav().handlers.release(70)
    expect(wrapper.emitted('select')).toEqual([['reels']])
    await flushPromises()
    expect(nav().bubble).toEqual(BOXES.reels)
  })

  it('wobbles instead of selecting the active item again', async () => {
    const { wrapper, nav } = await mountNavigation()
    nav().handlers.release(10)
    await flushPromises()
    expect(wrapper.emitted('select')).toBeUndefined()
    expect(nav().wobbles).toBe(1)
  })

  it('skips items it may not select', async () => {
    const { wrapper, nav } = await mountNavigation({ canSelect: (key) => key !== 'reels' })
    nav().handlers.release(70)
    expect(wrapper.emitted('select')).toBeUndefined()
  })

  it('takes the width of a fixed item while dragging', async () => {
    const { nav } = await mountNavigation({ widthOf: 'reels' })
    nav().handlers.move(25, 0)
    await flushPromises()
    expect(nav().bubble).toEqual({ left: 0, width: 50 })
  })
})

import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import AddButton from '@/components/common/AddButton.vue'
import FloatingAddButton from '@/components/common/FloatingAddButton.vue'

describe('AddButton', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('keeps the floating button in place while pages swap their action', async () => {
    const floating = mount(FloatingAddButton)
    const home = mount(AddButton, { props: { label: 'Posten' } })
    await floating.vm.$nextTick()
    const element = floating.find('button').element

    home.unmount()
    const onClick = vi.fn()
    const album = mount(AddButton, {
      props: { label: 'Zur Timeline', icon: 'rectangle-history-circle-plus', loading: true },
      attrs: { onClick },
    })
    await floating.vm.$nextTick()
    expect(floating.find('button').element).toBe(element)
    expect(floating.find('button').attributes('title')).toBe('Zur Timeline')
    expect(floating.find('.loading').exists()).toBe(true)
    await floating.find('button').trigger('click')
    expect(onClick).not.toHaveBeenCalled()

    await album.setProps({ loading: false })
    expect(floating.find('.loading').exists()).toBe(false)
    await floating.find('button').trigger('click')
    expect(onClick).toHaveBeenCalledOnce()

    album.unmount()
    await floating.vm.$nextTick()
    expect(floating.find('button').exists()).toBe(false)
  })
})

import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it } from 'vitest'
import SelectMenu from '@core/components/SelectMenu.vue'

const options = [
  { value: 'public', label: 'Öffentlich', icon: 'globe' },
  { value: 'friends', label: 'Nur Freunde', icon: 'users' },
]

function mountMenu() {
  return mount(SelectMenu, {
    props: { modelValue: 'public', options, label: 'Profil sichtbar für' },
    attachTo: document.body,
  })
}

function listbox() {
  return document.body.querySelector('[role="listbox"]')
}

describe('SelectMenu', () => {
  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('shows the current option like a select field', () => {
    const wrapper = mountMenu()
    expect(wrapper.find('button.select').text()).toBe('Öffentlich')
    expect(listbox()).toBeNull()
  })

  it('emits the chosen option and closes', async () => {
    const wrapper = mountMenu()
    await wrapper.find('button.select').trigger('click')
    const choices = listbox().querySelectorAll('[role="option"]')
    expect(choices).toHaveLength(2)
    expect(choices[0].getAttribute('aria-selected')).toBe('true')
    choices[1].click()
    await flushPromises()
    expect(wrapper.emitted('update:modelValue')).toEqual([['friends']])
    expect(listbox()).toBeNull()
  })

  it('does not emit when the current option is chosen again', async () => {
    const wrapper = mountMenu()
    await wrapper.find('button.select').trigger('click')
    listbox().querySelector('[role="option"]').click()
    await flushPromises()
    expect(wrapper.emitted('update:modelValue')).toBeUndefined()
  })

  it('closes when clicking outside', async () => {
    const wrapper = mountMenu()
    await wrapper.find('button.select').trigger('click')
    document.body.querySelector('.fixed.inset-0').click()
    await flushPromises()
    expect(listbox()).toBeNull()
  })
})

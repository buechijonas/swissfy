import { beforeEach, describe, expect, it } from 'vitest'
import { mount, RouterLinkStub } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import VisibilityPicker from '@/components/posts/VisibilityPicker.vue'
import { useAuthStore } from '@/stores/auth.js'
import { useGroupsStore } from '@/stores/posts.js'

const GROUPS = [
  { id: 1, name: 'Familie' },
  { id: 2, name: 'Arbeit' },
]

function mountPicker(props = {}) {
  return mount(VisibilityPicker, {
    props: { visibility: 'public', groups: [], ...props },
    global: { stubs: { RouterLink: RouterLinkStub } },
  })
}

function labels(wrapper) {
  return wrapper.findAll('button').map((button) => button.text())
}

describe('VisibilityPicker', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    useGroupsStore().items = GROUPS
  })

  it.each([
    ['default', {}, { role: 'default' }, ['Alle', 'Follower', 'Freunde', 'Gruppen']],
    ['admin', {}, { role: 'admin' }, ['Alle', 'Follower', 'Freunde', 'Gruppen', 'Global']],
    ['moderator', {}, { role: 'moderator' }, ['Alle', 'Follower', 'Freunde', 'Gruppen']],
    [
      'admin story',
      { allowGlobal: false },
      { role: 'admin' },
      ['Alle', 'Follower', 'Freunde', 'Gruppen'],
    ],
    [
      'admin picture',
      { allowPublic: false },
      { role: 'admin' },
      ['Follower', 'Freunde', 'Gruppen'],
    ],
    ['logged out', {}, null, ['Alle', 'Follower', 'Freunde', 'Gruppen']],
  ])('shows the right options for %s', (_, props, user, expected) => {
    useAuthStore().user = user
    expect(labels(mountPicker(props))).toEqual(expected)
  })

  it('emits the chosen visibility', async () => {
    const wrapper = mountPicker()
    await wrapper.findAll('button')[2].trigger('click')
    expect(wrapper.emitted('update:visibility')).toEqual([['friends']])
  })

  it('explains global posts', () => {
    useAuthStore().user = { role: 'admin' }
    expect(mountPicker({ visibility: 'global' }).text()).toContain('Erscheint bei allen')
  })

  it('lists groups as checkboxes only for group visibility', () => {
    expect(mountPicker().findAll('input[type="checkbox"]')).toHaveLength(0)
    expect(mountPicker({ visibility: 'groups' }).findAll('input[type="checkbox"]')).toHaveLength(2)
  })

  it.each([
    [[], 1, true, [1]],
    [[1], 1, false, []],
    [[1], 2, true, [1, 2]],
    [[1, 2], 1, false, [2]],
  ])('toggles group %#', async (selected, id, checked, groups) => {
    const wrapper = mountPicker({ visibility: 'groups', groups: selected })
    const box = wrapper.findAll('input[type="checkbox"]')[id - 1]
    box.element.checked = checked
    await box.trigger('change')
    expect(wrapper.emitted('update:groups')).toEqual([[groups]])
  })

  it('links to group settings without groups', () => {
    useGroupsStore().items = []
    const wrapper = mountPicker({ visibility: 'groups' })
    expect(wrapper.text()).toContain('Du hast noch keine Gruppen.')
    expect(wrapper.findComponent(RouterLinkStub).props('to')).toBe('/settings?tab=groups')
  })
})

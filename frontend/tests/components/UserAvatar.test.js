import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import UserAvatar from '@/components/common/UserAvatar.vue'
import { icons } from '@/assets/icons.js'
import { avatars } from '@/assets/images.js'

const animal = Object.keys(avatars)[0]

function classes(props) {
  return mount(UserAvatar, { props }).classes()
}

describe('UserAvatar', () => {
  it.each([
    [{ picture: '/pic.webp' }, '/pic.webp'],
    [{ avatar: animal }, avatars[animal]],
    [{}, icons.user],
    [null, icons.user],
  ])('picks the source for %j', (user, src) => {
    expect(mount(UserAvatar, { props: { user } }).attributes('src')).toBe(src)
  })

  it('crops uploaded pictures to a circle', () => {
    expect(classes({ user: { picture: '/pic.webp' } })).toContain('object-cover')
    expect(classes({ user: { avatar: animal } })).not.toContain('object-cover')
  })

  it.each([
    [false, false, []],
    [true, false, ['ring-primary']],
    [true, true, ['ring-swissfy-muted']],
    [false, true, []],
  ])('ring=%s seen=%s', (storyRing, storySeen, expected) => {
    const result = classes({ user: {}, storyRing, storySeen })
    for (const ring of ['ring-primary', 'ring-swissfy-muted']) {
      expect(result.includes(ring)).toBe(expected.includes(ring))
    }
  })
})

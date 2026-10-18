import { describe, expect, it } from 'vitest'
import { avatars } from '@/assets/images.js'
import { connectionTitle } from '@/data/connections.js'
import { avatarSrc } from '@/lib/avatar.js'
import { searchQuery } from '@/lib/search.js'
import { pageTitle } from '@/lib/title.js'

describe('searchQuery', () => {
  it.each([
    [undefined, ''],
    ['', ''],
    ['a', ''],
    ['  a  ', ''],
    ['ab', 'ab'],
    ['  anna  ', 'anna'],
    ['#zürich', '#zürich'],
  ])('turns %j into %j', (q, expected) => {
    expect(searchQuery({ query: q === undefined ? {} : { q } })).toBe(expected)
  })
})

describe('pageTitle', () => {
  it('returns static titles', () => {
    expect(pageTitle({ meta: { title: 'Seeds' } })).toBe('Seeds')
  })

  it('evaluates dynamic titles with the route', () => {
    const route = { meta: { title: (r) => `@${r.params.username}` }, params: { username: 'anna' } }
    expect(pageTitle(route)).toBe('@anna')
  })

  it('is empty without a title', () => {
    expect(pageTitle({ meta: {} })).toBeUndefined()
  })
})

describe('connectionTitle', () => {
  it.each([
    ['followers', '@anna Follower'],
    ['following', '@anna folgt'],
    ['friends', '@anna Freunde'],
  ])('titles %s', (connection, expected) => {
    expect(connectionTitle({ params: { username: 'anna', connection } })).toBe(expected)
  })
})

describe('avatarSrc', () => {
  const animal = Object.keys(avatars)[0]

  it('prefers an uploaded picture', () => {
    expect(avatarSrc({ picture: '/pic.webp', avatar: animal })).toBe('/pic.webp')
  })

  it('falls back to the govex animal', () => {
    expect(avatarSrc({ picture: null, avatar: animal })).toBe(avatars[animal])
  })

  it.each([null, undefined, {}, { avatar: 'unknown' }, { avatar: '../../etc/passwd' }])(
    'has no source for %j',
    (user) => {
      expect(avatarSrc(user)).toBeUndefined()
    },
  )
})

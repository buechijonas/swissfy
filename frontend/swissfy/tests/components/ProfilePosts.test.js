import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import ProfilePosts from '@/components/profile/ProfilePosts.vue'

function mountPosts({ timeline = false, media = { pictures: true, reels: true }, query = {} }) {
  return mount(ProfilePosts, {
    props: { profile: { username: 'anna', media }, timeline },
    global: {
      stubs: { PostList: true, BaseSwitcher: true },
      mocks: { $route: { query }, $router: { replace: () => {} } },
    },
  })
}

function postList(wrapper) {
  return wrapper.findComponent({ name: 'PostList' })
}

describe('ProfilePosts', () => {
  it.each([
    [{}, '/api/posts/users/anna/?images=1'],
    [{ media: 'clips' }, '/api/posts/users/anna/?videos=1'],
    [{ media: 'unknown' }, '/api/posts/users/anna/?images=1'],
  ])('shows the tiles for %o from %s', (query, url) => {
    const wrapper = mountPosts({ query })
    expect(postList(wrapper).props('url')).toBe(url)
    expect(postList(wrapper).props('grid')).toBe(true)
  })

  it('falls back to reels when the profile has no pictures', () => {
    const wrapper = mountPosts({ media: { pictures: false, reels: true } })
    expect(postList(wrapper).props('url')).toBe('/api/posts/users/anna/?videos=1')
    expect(wrapper.findComponent({ name: 'BaseSwitcher' }).exists()).toBe(false)
  })

  it.each([
    [{}, '/api/posts/users/anna/activities/'],
    [{ activity: 'comments' }, '/api/posts/users/anna/activities/?comments=1'],
  ])('shows the activities for %o from %s', (query, url) => {
    const wrapper = mountPosts({ timeline: true, query })
    expect(postList(wrapper).props('url')).toBe(url)
    expect(postList(wrapper).props('edgeToEdge')).toBe(true)
    expect(wrapper.findComponent({ name: 'BaseSwitcher' }).props('active')).toBe(
      query.activity ?? 'feeds',
    )
  })
})

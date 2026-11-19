import { flushPromises, mount, RouterLinkStub } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import profilesApi from '@/api/profiles.js'
import ProfileHeader from '@/components/profile/ProfileHeader.vue'
import { t } from '@/i18n.js'

vi.mock('@/api/profiles.js', () => ({
  default: { follow: vi.fn(), unfollow: vi.fn(), requestFriendship: vi.fn() },
}))

function profile(overrides = {}) {
  return {
    username: 'anna',
    display_name: 'Anna',
    role: 'user',
    can_view: true,
    can_chat: true,
    is_self: false,
    is_following: false,
    follow_requested: false,
    requires_follow_request: false,
    is_friend: false,
    follows_you: false,
    friend_request_sent: false,
    follower_count: 3,
    following_count: 4,
    friend_count: 5,
    stories: [],
    ...overrides,
  }
}

function mountHeader(overrides) {
  return mount(ProfileHeader, {
    props: { profile: profile(overrides) },
    global: {
      stubs: { RouterLink: RouterLinkStub, UserAvatar: true },
      mocks: { $router: { push: vi.fn() } },
    },
  })
}

function connectionLinks(wrapper) {
  return wrapper
    .findAllComponents(RouterLinkStub)
    .filter((link) => link.props('to').startsWith('/profile/'))
}

function button(wrapper, label) {
  return wrapper.findAll('button').find((item) => item.text().includes(label))
}

describe('ProfileHeader', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('links the counts to the connections of the profile', () => {
    const links = connectionLinks(mountHeader())
    expect(links.map((link) => link.props('to'))).toEqual([
      '/profile/anna/followers',
      '/profile/anna/following',
      '/profile/anna/friends',
    ])
    expect(links.map((link) => link.text())).toEqual([
      expect.stringContaining('3'),
      expect.stringContaining('4'),
      expect.stringContaining('5'),
    ])
  })

  it('hides counts and links of private profiles', () => {
    const wrapper = mountHeader({ can_view: false })
    expect(connectionLinks(wrapper)).toHaveLength(0)
    expect(wrapper.text()).toContain(t('profile.private'))
  })

  it.each([
    [{}, 'profile.follow'],
    [{ requires_follow_request: true }, 'profile.request'],
    [{ follow_requested: true }, 'profile.requested'],
    [{ is_following: true }, 'profile.unfollow'],
  ])('labels the follow button for %o as %s', (state, label) => {
    expect(button(mountHeader(state), t(label))).toBeTruthy()
  })

  it('follows and hands the updated profile to the parent', async () => {
    const updated = profile({ is_following: true })
    profilesApi.follow.mockResolvedValue(updated)
    const wrapper = mountHeader()
    await button(wrapper, t('profile.follow')).trigger('click')
    await flushPromises()
    expect(profilesApi.follow).toHaveBeenCalledWith('anna')
    expect(wrapper.emitted('update:profile')).toEqual([[updated]])
  })

  it.each([{ is_following: true }, { follow_requested: true }])(
    'unfollows when %o',
    async (state) => {
      profilesApi.unfollow.mockResolvedValue(profile())
      const wrapper = mountHeader(state)
      await button(
        wrapper,
        t(state.is_following ? 'profile.unfollow' : 'profile.requested'),
      ).trigger('click')
      await flushPromises()
      expect(profilesApi.unfollow).toHaveBeenCalledWith('anna')
    },
  )

  it('shows the error of a failed action and keeps the profile', async () => {
    profilesApi.follow.mockRejectedValue({ detail: 'Gesperrt' })
    const wrapper = mountHeader()
    await button(wrapper, t('profile.follow')).trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('Gesperrt')
    expect(wrapper.emitted('update:profile')).toBeUndefined()
  })

  it.each([
    [{ is_following: true, follows_you: true }, true],
    [{ is_following: true, follows_you: false }, false],
    [{ is_following: false, follows_you: true }, false],
    [{ is_following: true, follows_you: true, is_friend: true }, false],
  ])('offers a friend request for %o: %s', (state, expected) => {
    expect(Boolean(button(mountHeader(state), t('profile.request')))).toBe(expected)
  })

  it('sends a friend request', async () => {
    profilesApi.requestFriendship.mockResolvedValue(profile({ friend_request_sent: true }))
    const wrapper = mountHeader({ is_following: true, follows_you: true })
    await button(wrapper, t('profile.request')).trigger('click')
    await flushPromises()
    expect(profilesApi.requestFriendship).toHaveBeenCalledWith('anna')
  })

  it('offers editing instead of actions on the own profile', () => {
    const wrapper = mountHeader({ is_self: true })
    expect(button(wrapper, t('profile.follow'))).toBeUndefined()
    expect(wrapper.find('[title="' + t('common.edit') + '"]').exists()).toBe(true)
  })

  it('opens the stories through the parent', async () => {
    const wrapper = mountHeader({ stories: [{ id: 1, seen: false }] })
    await wrapper.find(`[title="${t('profile.viewStory')}"]`).trigger('click')
    expect(wrapper.emitted('open-story')).toHaveLength(1)
  })
})

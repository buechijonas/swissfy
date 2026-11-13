import { describe, expect, it } from 'vitest'
import { mount, RouterLinkStub } from '@vue/test-utils'
import BaseButton from '@core/components/BaseButton.vue'
import PostText from '@/components/posts/PostText.vue'
import LoginView from '@/views/auth/LoginView.vue'
import { extractHashtags, hashtagLink } from '@/lib/hashtags.js'

const PAYLOADS = [
  '<script>alert(1)</script>',
  '<img src=x onerror=alert(1)>',
  '<svg onload=alert(1)>',
  '"><iframe src=javascript:alert(1)>',
  '{{ constructor.constructor("alert(1)")() }}',
]

function mountPostText(...parts) {
  return mount(PostText, {
    props: { parts },
    global: { stubs: { RouterLink: RouterLinkStub } },
  })
}

function textPart(text) {
  return { start: 0, text, hashtag: null }
}

describe('PostText', () => {
  it.each(PAYLOADS)('renders %s as text', (payload) => {
    const wrapper = mountPostText(textPart(`Hallo ${payload} `), {
      start: 7 + payload.length,
      text: '#swiss',
      hashtag: 'swiss',
    })
    expect(wrapper.find('script').exists()).toBe(false)
    expect(wrapper.find('img').exists()).toBe(false)
    expect(wrapper.find('svg').exists()).toBe(false)
    expect(wrapper.find('iframe').exists()).toBe(false)
    expect(wrapper.text()).toContain(payload)
  })

  it('does not evaluate template syntax in user text', () => {
    const wrapper = mountPostText(textPart('{{ 7 * 7 }}'))
    expect(wrapper.text()).toBe('{{ 7 * 7 }}')
  })

  it('links hashtags only to the hashtag route', () => {
    const wrapper = mountPostText({ start: 0, text: '#Swiss', hashtag: 'swiss' })
    expect(wrapper.findComponent(RouterLinkStub).props('to')).toBe('/hashtags/swiss')
  })
})

describe('hashtags', () => {
  it('encodes hashtag links so they stay inside /hashtags/', () => {
    expect(hashtagLink('../../admin')).toBe('/hashtags/..%2F..%2Fadmin')
    expect(hashtagLink('a?b#c')).toBe('/hashtags/a%3Fb%23c')
  })

  it('only extracts word characters', () => {
    expect(extractHashtags('#ok<script> #a"b #javascript:alert(1)')).toEqual([
      'ok',
      'a',
      'javascript',
    ])
  })
})

describe('BaseButton', () => {
  function mountButton(props) {
    return mount(BaseButton, {
      props,
      slots: { default: 'Go' },
      global: { stubs: { RouterLink: RouterLinkStub } },
    })
  }

  it.each(['javascript:alert(1)', 'data:text/html,x', 'vbscript:x', '//evil.example'])(
    'never renders %s as href',
    (href) => {
      const wrapper = mountButton({ href })
      expect(wrapper.find('a').exists()).toBe(false)
      expect(wrapper.html()).not.toContain(href)
    },
  )

  it('renders safe external links', () => {
    const wrapper = mountButton({ href: 'https://swissfy.ch', rel: 'noopener' })
    expect(wrapper.find('a').attributes('href')).toBe('https://swissfy.ch')
  })
})

describe('LoginView', () => {
  function mountLogin(error) {
    return mount(LoginView, {
      global: {
        mocks: { $route: { query: { error } } },
        stubs: { AuthPage: { template: '<div><slot /></div>' }, BaseButton: true },
      },
    })
  }

  it('shows known errors', () => {
    expect(mountLogin('oidc_failed').text()).toContain('fehlgeschlagen')
  })

  it.each(['constructor', '__proto__', 'toString', 'hasOwnProperty', PAYLOADS[1]])(
    'ignores unknown error key %s',
    (error) => {
      const wrapper = mountLogin(error)
      expect(wrapper.find('.text-error').exists()).toBe(false)
      expect(wrapper.html()).not.toContain('native code')
    },
  )
})

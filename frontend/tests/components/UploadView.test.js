import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount, RouterLinkStub } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import UploadView from '@/views/UploadView.vue'
import { useGroupsStore } from '@/stores/posts.js'

async function mountUpload(kind, remaining = 3) {
  vi.stubGlobal(
    'fetch',
    vi.fn(() =>
      Promise.resolve(new Response(JSON.stringify({ remaining, limit: 10 }), { status: 200 })),
    ),
  )
  const wrapper = mount(UploadView, {
    global: {
      stubs: {
        RouterLink: RouterLinkStub,
        BaseBreadcrumbs: true,
        BaseFooter: true,
        ImageDropzone: true,
      },
      mocks: {
        $route: { params: { kind }, path: `/upload/${kind}`, meta: { title: 'Neu' } },
        $router: { back: vi.fn(), replace: vi.fn() },
      },
    },
  })
  await flushPromises()
  return wrapper
}

const image = { blob: new Blob(['x']), preview: 'blob:x', width: 1, height: 1 }

describe('UploadView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    useGroupsStore().items = [{ id: 1, name: 'Familie' }]
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  const feedCases = []
  for (const terms of [true, false]) {
    for (const content of ['none', 'text', 'image']) {
      for (const audience of ['public', 'groups-empty', 'groups-picked']) {
        for (const remaining of [3, 0]) {
          const expected =
            terms && content !== 'none' && audience !== 'groups-empty' && remaining > 0
          feedCases.push([terms, content, audience, remaining, expected])
        }
      }
    }
  }

  it.each(feedCases)(
    'feed terms=%s content=%s audience=%s remaining=%s → %s',
    async (terms, content, audience, remaining, expected) => {
      const wrapper = await mountUpload('feed', remaining)
      wrapper.vm.acceptedTerms = terms
      if (content === 'text') wrapper.vm.text = 'Hallo'
      if (content === 'image') wrapper.vm.images = [image]
      if (audience !== 'public') wrapper.vm.visibility = 'groups'
      if (audience === 'groups-picked') wrapper.vm.selectedGroups = [1]
      expect(wrapper.vm.canSubmit).toBe(expected)
    },
  )

  const storyCases = []
  for (const terms of [true, false]) {
    for (const hasImage of [true, false]) {
      for (const text of ['', 'Hallo']) {
        storyCases.push([terms, hasImage, text, terms && hasImage])
      }
    }
  }

  it.each(storyCases)(
    'story terms=%s image=%s text=%j → %s',
    async (terms, hasImage, text, expected) => {
      const wrapper = await mountUpload('story')
      wrapper.vm.acceptedTerms = terms
      wrapper.vm.text = text
      if (hasImage) wrapper.vm.storyImage = { blob: new Blob(['x']), preview: 'blob:x' }
      expect(wrapper.vm.canSubmit).toBe(expected)
    },
  )

  it('limits story text to 200 and feed text to 500 characters', async () => {
    expect((await mountUpload('story')).find('textarea').attributes('maxlength')).toBe('200')
    expect((await mountUpload('feed')).find('textarea').attributes('maxlength')).toBe('500')
  })

  it('never offers global visibility for stories', async () => {
    const wrapper = await mountUpload('story')
    expect(wrapper.text()).not.toContain('Global')
  })

  it('posts stories to the story endpoint', async () => {
    const wrapper = await mountUpload('story')
    wrapper.vm.acceptedTerms = true
    wrapper.vm.storyImage = { blob: new Blob(['x']), preview: 'blob:x' }
    await wrapper.vm.submit()
    const [url, options] = fetch.mock.calls.at(-1)
    expect(url).toBe('/api/stories/')
    expect(options.body.get('image')).toBeTruthy()
    expect(options.body.get('visibility')).toBe('public')
  })
})

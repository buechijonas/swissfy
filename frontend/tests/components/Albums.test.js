import { afterEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount, RouterLinkStub } from '@vue/test-utils'
import AddPostsDialog from '@/components/albums/AddPostsDialog.vue'
import AlbumTimeline from '@/components/albums/AlbumTimeline.vue'
import ProfileAlbums from '@/components/albums/ProfileAlbums.vue'

const albums = [
  { id: 'a1', name: 'Ferien', cover: '/api/posts/p1/thumbnail/' },
  { id: 'a2', name: 'Familie', cover: null },
]

function respond(data) {
  return Promise.resolve(new Response(JSON.stringify(data), { status: 200 }))
}

async function mountAlbums(editable) {
  const fetch = vi.fn((url, options) =>
    respond(options?.method === 'PUT' ? [albums[1], albums[0]] : albums),
  )
  vi.stubGlobal('fetch', fetch)
  const wrapper = mount(ProfileAlbums, {
    props: { username: 'anna', editable },
    global: { stubs: { RouterLink: RouterLinkStub, AlbumDialog: true } },
    attachTo: document.body,
  })
  await flushPromises()
  return { wrapper, fetch }
}

function albumIds(wrapper) {
  return wrapper.findAll('[data-album]').map((tile) => tile.attributes('data-album'))
}

async function dragOnto(wrapper, handle, target) {
  handle.element.setPointerCapture = () => {}
  document.elementFromPoint = () => target.element
  await handle.trigger('pointerdown', { pointerId: 1 })
  await handle.trigger('pointermove')
}

function entry(id) {
  return {
    id,
    date: '2019-07-14',
    title: `Titel ${id}`,
    post: {
      id: `post-${id}`,
      thumbnail: `/${id}.webp`,
      video: false,
      author: { username: 'anna' },
    },
  }
}

afterEach(() => {
  vi.unstubAllGlobals()
  document.elementFromPoint = undefined
  document.body.innerHTML = ''
})

describe('ProfileAlbums', () => {
  it('shows the create tile first and new albums right after it', async () => {
    const { wrapper } = await mountAlbums(true)
    expect(wrapper.find('.grid').element.firstElementChild.getAttribute('title')).toBe(
      'Neues Album',
    )
    expect(albumIds(wrapper)).toEqual(['a1', 'a2'])

    wrapper.vm.addAlbum({ id: 'a3', name: 'Neu', cover: null })
    await wrapper.vm.$nextTick()
    expect(albumIds(wrapper)).toEqual(['a3', 'a1', 'a2'])
  })

  it('saves the dragged album order', async () => {
    const { wrapper, fetch } = await mountAlbums(true)
    const handle = wrapper.findAll('[title="Verschieben"]')[0]
    await dragOnto(wrapper, handle, wrapper.findAll('[data-album]')[1])
    expect(albumIds(wrapper)).toEqual(['a2', 'a1'])

    await handle.trigger('pointerup')
    await flushPromises()
    const [url, options] = fetch.mock.calls.at(-1)
    expect(url).toBe('/api/albums/order/')
    expect(JSON.parse(options.body)).toEqual({ albums: ['a2', 'a1'] })
    expect(albumIds(wrapper)).toEqual(['a2', 'a1'])
  })

  it('hides create tile and drag handles on foreign profiles', async () => {
    const { wrapper } = await mountAlbums(false)
    expect(wrapper.find('[title="Neues Album"]').exists()).toBe(false)
    expect(wrapper.find('[title="Verschieben"]').exists()).toBe(false)
  })
})

describe('AlbumTimeline', () => {
  function mountTimeline(entries, editable = false) {
    return mount(AlbumTimeline, {
      props: { entries, editable },
      global: { stubs: { RouterLink: RouterLinkStub } },
    })
  }

  it('shows the chosen date and marks undated posts', () => {
    const wrapper = mountTimeline([entry('e1'), { ...entry('e2'), date: null }])
    const items = wrapper.findAll('[data-entry]')
    expect(items[0].find('time').attributes('datetime')).toBe('2019-07-14')
    expect(items[0].find('time').text()).toBe('14. Juli 2019')
    expect(items[1].find('time').exists()).toBe(false)
    expect(items[1].text()).toContain('Ohne Datum')
  })

  it('offers adding and editing only to the owner', async () => {
    expect(
      mountTimeline([entry('e1')])
        .find('button')
        .exists(),
    ).toBe(false)
    const wrapper = mountTimeline([entry('e1')], true)
    await wrapper.find('[title="Bearbeiten"]').trigger('click')
    expect(wrapper.emitted('edit-entry')[0][0].id).toBe('e1')
  })
})

describe('AddPostsDialog', () => {
  it('adds several existing posts with optional dates', async () => {
    const posts = ['p1', 'p2', 'p3'].map((id) => ({ id, thumbnail: `/${id}.webp` }))
    const fetch = vi.fn((url, options) =>
      respond(options?.method === 'POST' ? { id: 'a1' } : { results: posts, next: null }),
    )
    vi.stubGlobal('fetch', fetch)
    HTMLDialogElement.prototype.showModal = () => {}
    HTMLDialogElement.prototype.close = () => {}
    const album = { id: 'a1', owner: 'anna', entries: [{ post: { id: 'p3' } }] }
    const wrapper = mount(AddPostsDialog, { props: { album } })
    wrapper.vm.open()
    await flushPromises()

    expect(fetch.mock.calls[0][0]).toBe('/api/posts/users/anna/?media=1')
    const picks = wrapper.findAll('[data-pick]')
    expect(picks).toHaveLength(2)
    await picks[1].trigger('click')
    await picks[0].trigger('click')
    await wrapper
      .findAll('button')
      .find((b) => b.text().startsWith('Weiter'))
      .trigger('click')

    await wrapper.find('input[type="date"]').setValue('2003-05-01')
    await wrapper
      .findAll('button')
      .find((b) => b.text() === 'Hinzufügen')
      .trigger('click')
    await flushPromises()

    const [url, options] = fetch.mock.calls.at(-1)
    expect(url).toBe('/api/albums/a1/entries/')
    expect(JSON.parse(options.body)).toEqual({
      entries: [
        { post: 'p2', date: '2003-05-01', title: '' },
        { post: 'p1', date: null, title: '' },
      ],
    })
    expect(wrapper.emitted('saved')[0][0]).toEqual({ id: 'a1' })
  })
})

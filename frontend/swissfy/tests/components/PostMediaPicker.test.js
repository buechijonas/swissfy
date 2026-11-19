import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import PostMediaPicker from '@/components/posts/PostMediaPicker.vue'
import { t } from '@/i18n.js'
import { compressImage, imageSize } from '@/lib/image.js'
import { MAX_VIDEO_DURATION, MAX_VIDEO_SIZE, videoDuration } from '@/lib/video.js'

vi.mock('@/lib/image.js', () => ({ compressImage: vi.fn(), imageSize: vi.fn() }))
vi.mock('@/lib/video.js', async (importOriginal) => ({
  ...(await importOriginal()),
  videoDuration: vi.fn(),
}))

function file(name, type, size = 1) {
  return { name, type, size }
}

function image(preview) {
  return { blob: new Blob(['x']), preview, width: 1, height: 1 }
}

function mountPicker(images = [], video = null) {
  return mount(PostMediaPicker, {
    props: { images, video },
    global: { stubs: { ImageDropzone: true } },
  })
}

async function drop(wrapper, files) {
  wrapper.findComponent({ name: 'ImageDropzone' }).vm.$emit('select', files)
  await flushPromises()
}

describe('PostMediaPicker', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.stubGlobal('URL', { createObjectURL: vi.fn(() => 'blob:preview'), revokeObjectURL: vi.fn() })
    compressImage.mockImplementation((source) => Promise.resolve(new Blob([source.name])))
    imageSize.mockResolvedValue({ width: 4, height: 3 })
    videoDuration.mockResolvedValue(10)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('adds all dropped images at once', async () => {
    const wrapper = mountPicker()
    await drop(wrapper, [file('a.jpg', 'image/jpeg'), file('b.jpg', 'image/jpeg')])
    const [[images]] = wrapper.emitted('update:images')
    expect(images).toHaveLength(2)
    expect(images[0]).toMatchObject({ width: 4, height: 3, preview: 'blob:preview' })
  })

  it('takes only as many images as still fit', async () => {
    const existing = Array.from({ length: 9 }, (_, index) => image(`blob:${index}`))
    const wrapper = mountPicker(existing)
    await drop(wrapper, [file('a.jpg', 'image/jpeg'), file('b.jpg', 'image/jpeg')])
    expect(wrapper.emitted('update:images')[0][0]).toHaveLength(10)
    expect(wrapper.text()).toContain(t('upload.tooManyImages', { count: 10 }))
  })

  it('skips unreadable images and keeps the readable ones', async () => {
    compressImage.mockRejectedValueOnce(new Error('broken'))
    const wrapper = mountPicker()
    await drop(wrapper, [file('a.jpg', 'image/jpeg'), file('b.jpg', 'image/jpeg')])
    expect(wrapper.emitted('update:images')[0][0]).toHaveLength(1)
    expect(wrapper.text()).toContain(t('upload.anImageUnreadable'))
  })

  it.each(['video/mp4', ''])('picks a video by type %j or file extension', async (type) => {
    const wrapper = mountPicker()
    await drop(wrapper, [file('a.jpg', 'image/jpeg'), file('clip.mov', type)])
    expect(wrapper.emitted('update:video')[0][0]).toMatchObject({ preview: 'blob:preview' })
    expect(wrapper.emitted('update:images')).toBeUndefined()
  })

  it('rejects videos that are too large', async () => {
    const wrapper = mountPicker()
    await drop(wrapper, [file('clip.mp4', 'video/mp4', MAX_VIDEO_SIZE + 1)])
    expect(wrapper.emitted('update:video')).toBeUndefined()
    expect(wrapper.text()).toContain(t('upload.videoTooLarge'))
  })

  it('rejects videos that are too long and frees their preview', async () => {
    videoDuration.mockResolvedValue(MAX_VIDEO_DURATION + 1)
    const wrapper = mountPicker()
    await drop(wrapper, [file('clip.mp4', 'video/mp4')])
    expect(wrapper.emitted('update:video')).toBeUndefined()
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:preview')
  })

  it('removes an image and frees its preview', async () => {
    const first = image('blob:1')
    const wrapper = mountPicker([first, image('blob:2')])
    await wrapper.find(`[title="${t('upload.removeImage')}"]`).trigger('click')
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:1')
    expect(wrapper.emitted('update:images')[0][0]).toHaveLength(1)
  })

  it('frees all previews when it is closed', () => {
    const wrapper = mountPicker([image('blob:1')])
    wrapper.unmount()
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:1')
  })
})

<template>
  <div v-if="video" class="relative">
    <video
      :src="video.preview"
      class="max-h-80 w-full rounded-box bg-black object-contain"
      controls
      playsinline
    ></video>
    <BaseButton
      variant="neutral"
      shape="circle"
      size="sm"
      class="absolute top-2 right-2"
      :title="$t('upload.removeVideo')"
      @click="clearVideo"
    >
      <AppIcon name="cross" :alt="$t('upload.removeVideo')" />
    </BaseButton>
  </div>
  <ImageDropzone
    v-else-if="!images.length"
    class="h-56"
    accept="image/*,video/*,video/mp4,video/quicktime,video/x-matroska,.mov,.mp4,.mkv"
    :label="$t('upload.postDrop')"
    multiple
    @select="addMedia"
  />
  <div v-else class="flex gap-2 overflow-x-auto">
    <div
      v-for="image in images"
      :key="image.preview"
      class="relative h-40 max-w-full shrink-0"
      :style="{ aspectRatio: `${image.width} / ${image.height}` }"
    >
      <img :src="image.preview" alt="" class="size-full rounded-box bg-base-200 object-cover" />
      <BaseButton
        variant="neutral"
        shape="circle"
        size="sm"
        class="absolute top-2 right-2"
        :title="$t('upload.removeImage')"
        @click="removeImage(image)"
      >
        <AppIcon name="cross" :alt="$t('upload.removeImage')" />
      </BaseButton>
    </div>
    <ImageDropzone
      v-if="images.length < maxImages"
      class="h-40 w-28 shrink-0"
      :label="$t('upload.add')"
      multiple
      @select="addImages"
    />
  </div>
  <p v-if="images.length > 1" class="mt-1 text-xs text-app-muted">
    {{ $t('upload.cropHint') }}
  </p>
  <p v-if="video" class="mt-1 text-xs text-app-muted">
    {{ $t('upload.videoHint') }}
  </p>
  <ErrorText :message="error" class="mt-2" />
</template>

<script>
import without from 'lodash-es/without'
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import ErrorText from '@core/components/ErrorText.vue'
import ImageDropzone from '@/components/common/ImageDropzone.vue'
import { t } from '@/i18n.js'
import { compressImage, imageSize } from '@/lib/image.js'
import { MAX_VIDEO_DURATION, MAX_VIDEO_SIZE, videoDuration } from '@/lib/video.js'

const MAX_IMAGES = 10

export default {
  name: 'PostMediaPicker',
  components: { AppIcon, BaseButton, ErrorText, ImageDropzone },
  props: {
    images: { type: Array, required: true },
    video: { type: Object, default: null },
  },
  emits: ['update:images', 'update:video'],
  data() {
    return { error: null, maxImages: MAX_IMAGES }
  },
  beforeUnmount() {
    for (const image of this.images) URL.revokeObjectURL(image.preview)
    if (this.video) URL.revokeObjectURL(this.video.preview)
  },
  methods: {
    addMedia(files) {
      const video = files.find(
        (file) => file.type.startsWith('video/') || /\.(mov|mp4|mkv)$/i.test(file.name),
      )
      return video ? this.setVideo(video) : this.addImages(files)
    },
    async setVideo(file) {
      this.error = null
      if (file.size > MAX_VIDEO_SIZE) {
        this.error = t('upload.videoTooLarge')
        return
      }
      const preview = URL.createObjectURL(file)
      const duration = await videoDuration(preview).catch(() => 0)
      if (duration > MAX_VIDEO_DURATION + 0.5) {
        URL.revokeObjectURL(preview)
        this.error = t('upload.videoTooLong', { seconds: MAX_VIDEO_DURATION })
        return
      }
      this.$emit('update:video', { file, preview })
    },
    clearVideo() {
      URL.revokeObjectURL(this.video.preview)
      this.$emit('update:video', null)
    },
    async addImages(files) {
      this.error = null
      const free = MAX_IMAGES - this.images.length
      if (files.length > free) this.error = t('upload.tooManyImages', { count: MAX_IMAGES })
      const added = []
      for (const file of files.slice(0, free)) {
        try {
          const blob = await compressImage(file)
          const size = await imageSize(blob)
          added.push({ blob, ...size, preview: URL.createObjectURL(blob) })
        } catch {
          this.error = t('upload.anImageUnreadable')
        }
      }
      this.$emit('update:images', [...this.images, ...added])
    },
    removeImage(image) {
      URL.revokeObjectURL(image.preview)
      this.$emit('update:images', without(this.images, image))
    },
  },
}
</script>

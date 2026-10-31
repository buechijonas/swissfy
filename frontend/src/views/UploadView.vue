<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div
    class="flex flex-1 flex-col bg-base-100 pb-8 px-6 max-h-[calc(100dvh-var(--mobile-chrome-height))] overflow-y-auto lg:max-h-none lg:overflow-y-visible"
  >
    <div class="flex w-full flex-1 flex-col pt-4">
      <template v-if="kind === 'story'">
        <div
          v-if="storyImage"
          class="relative mx-auto aspect-9/16 h-96 max-w-full overflow-hidden rounded-box bg-black"
        >
          <img :src="storyImage.preview" alt="" class="size-full object-contain" />
          <p
            v-if="text.trim()"
            class="absolute inset-x-0 bottom-0 whitespace-pre-line bg-black/50 px-4 py-3 text-center text-white"
          >
            {{ text }}
          </p>
          <BaseButton
            variant="neutral"
            shape="circle"
            size="sm"
            class="absolute top-2 right-2"
            title="Bild entfernen"
            @click="clearStoryImage"
          >
            <AppIcon name="cross" alt="Bild entfernen" />
          </BaseButton>
        </div>
        <ImageDropzone
          v-else
          class="h-56"
          label="Bild für deine Story hierher ziehen oder klicken"
          @select="setStoryImage"
        />
        <textarea
          v-model="text"
          class="textarea w-full h-20 resize-none mt-4"
          :maxlength="maxLength"
          placeholder="Text auf deiner Story (optional)"
        ></textarea>
        <p class="mt-2 text-right text-xs text-swissfy-muted">
          {{ text.length }} / {{ maxLength }}
        </p>
      </template>

      <template v-else>
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
            title="Video entfernen"
            @click="clearVideo"
          >
            <AppIcon name="cross" alt="Video entfernen" />
          </BaseButton>
        </div>
        <ImageDropzone
          v-else-if="!images.length"
          class="h-56"
          accept="image/*,video/*,video/mp4,video/quicktime,video/x-matroska,.mov,.mp4,.mkv"
          label="Bilder oder ein Video hierher ziehen oder klicken"
          multiple
          @select="addMedia"
        />
        <div v-else class="flex gap-2 overflow-x-auto">
          <div
            v-for="(image, index) in images"
            :key="image.preview"
            class="relative h-40 max-w-full shrink-0"
            :style="{ aspectRatio: `${image.width} / ${image.height}` }"
          >
            <img
              :src="image.preview"
              alt=""
              class="size-full object-cover rounded-box bg-base-200"
            />
            <BaseButton
              variant="neutral"
              shape="circle"
              size="sm"
              class="absolute top-2 right-2"
              title="Bild entfernen"
              @click="removeImage(index)"
            >
              <AppIcon name="cross" alt="Bild entfernen" />
            </BaseButton>
          </div>
          <ImageDropzone
            v-if="images.length < maxImages"
            class="h-40 w-28 shrink-0"
            label="Hinzufügen"
            multiple
            @select="addImages"
          />
        </div>
        <p v-if="images.length > 1" class="text-xs text-swissfy-muted mt-1">
          Alle Bilder werden im Format des ersten Bildes zugeschnitten.
        </p>
        <p v-if="video" class="text-xs text-swissfy-muted mt-1">
          Das Video wird nach dem Posten verarbeitet und erscheint danach für andere.
        </p>

        <textarea
          v-model="text"
          class="textarea w-full h-28 resize-none mt-4"
          :maxlength="maxLength"
          placeholder="Was gibt's Neues? Hashtags mit # markieren, z. B. #zürich"
        ></textarea>
        <div class="mt-2 flex items-start gap-2">
          <div class="flex min-w-0 flex-1 flex-wrap gap-1">
            <span
              v-for="hashtag in hashtags"
              :key="hashtag"
              class="badge badge-sm badge-soft badge-primary"
            >
              #{{ hashtag }}
            </span>
          </div>
          <p class="shrink-0 text-xs text-swissfy-muted">{{ text.length }} / {{ maxLength }}</p>
        </div>
      </template>

      <div class="mt-4">
        <VisibilityPicker
          v-model:visibility="visibility"
          v-model:groups="selectedGroups"
          :allow-global="kind === 'feed'"
        />
      </div>

      <p v-if="error" class="text-error text-sm mt-4">{{ error }}</p>

      <label class="mt-4 flex items-center gap-3 text-sm">
        <input v-model="acceptedTerms" type="checkbox" class="size-8 shrink-0 accent-primary" />
        <span>
          Ich bestätige, dass {{ kind === 'story' ? 'meine Story' : 'mein Feed' }} den
          <a href="/terms" target="_blank" rel="noopener" class="link text-primary"
            >Nutzungsrichtlinien</a
          >
          entspricht.
        </span>
      </label>
      <p
        v-if="quota && kind === 'feed'"
        class="text-sm mt-4"
        :class="quota.remaining ? 'text-swissfy-muted' : 'text-error'"
      >
        {{
          quota.remaining
            ? `Heute noch ${quota.remaining} von ${quota.limit} Feeds möglich.`
            : `Du hast heute bereits ${quota.limit} Feeds erstellt.`
        }}
      </p>

      <div class="mt-auto flex justify-end gap-2 pt-6">
        <BaseButton :disabled="sending" @click="leave">
          <AppIcon name="cross" />
          Abbrechen
        </BaseButton>
        <BaseButton variant="primary" :disabled="!canSubmit" @click="submit">
          <span v-if="sending" class="loading loading-spinner loading-sm"></span>
          <AppIcon v-else name="paper-plane-top" />
          {{ sending ? 'Wird gepostet…' : 'Posten' }}
        </BaseButton>
      </div>
    </div>
  </div>
  <BaseFooter />
</template>

<script>
import AppIcon from '@/components/common/AppIcon.vue'
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import ImageDropzone from '@/components/common/ImageDropzone.vue'
import VisibilityPicker from '@/components/posts/VisibilityPicker.vue'
import postsApi from '@/api/posts.js'
import storiesApi from '@/api/stories.js'
import { extractHashtags } from '@/lib/hashtags.js'
import { compressImage, imageSize } from '@/lib/image.js'
import { pageTitle } from '@/lib/title.js'
import { MAX_VIDEO_DURATION, MAX_VIDEO_SIZE, videoDuration } from '@/lib/video.js'
import { useGroupsStore } from '@/stores/posts.js'

const MAX_LENGTH = 500
const MAX_STORY_LENGTH = 200
const MAX_IMAGES = 10

export default {
  name: 'UploadView',
  components: {
    AppIcon,
    BaseBreadcrumbs,
    BaseButton,
    BaseFooter,
    ImageDropzone,
    VisibilityPicker,
  },
  data() {
    return {
      text: '',
      images: [],
      storyImage: null,
      video: null,
      quota: null,
      visibility: 'public',
      selectedGroups: [],
      acceptedTerms: false,
      sending: false,
      error: null,
      maxImages: MAX_IMAGES,
    }
  },
  computed: {
    kind() {
      return this.$route.params.kind
    },
    breadcrumbs() {
      return [{ label: pageTitle(this.$route), to: this.$route.path }]
    },
    maxLength() {
      return this.kind === 'story' ? MAX_STORY_LENGTH : MAX_LENGTH
    },
    hashtags() {
      return extractHashtags(this.text)
    },
    canSubmit() {
      const hasAudience = this.visibility !== 'groups' || this.selectedGroups.length
      if (this.sending || !this.acceptedTerms || !hasAudience) return false
      if (this.kind === 'story') return Boolean(this.storyImage)
      const hasContent = this.text.trim() !== '' || this.images.length > 0 || Boolean(this.video)
      return hasContent && this.quota?.remaining !== 0
    },
  },
  mounted() {
    useGroupsStore()
      .load()
      .catch(() => {})
    if (this.kind === 'feed') this.loadQuota()
  },
  beforeUnmount() {
    this.clearImages()
    this.clearVideo()
    this.clearStoryImage()
  },
  methods: {
    leave() {
      if (window.history.state?.back) {
        this.$router.back()
      } else {
        this.$router.replace(this.kind === 'story' ? '/profile' : '/')
      }
    },
    async setStoryImage([file]) {
      this.error = null
      try {
        const blob = await compressImage(file)
        this.clearStoryImage()
        this.storyImage = { blob, preview: URL.createObjectURL(blob) }
      } catch {
        this.error = 'Das Bild konnte nicht gelesen werden.'
      }
    },
    clearStoryImage() {
      if (this.storyImage) URL.revokeObjectURL(this.storyImage.preview)
      this.storyImage = null
    },
    async loadQuota() {
      try {
        this.quota = await postsApi.quota()
      } catch {
        this.quota = null
      }
    },
    addMedia(files) {
      const video = files.find(
        (file) => file.type.startsWith('video/') || /\.(mov|mp4|mkv)$/i.test(file.name),
      )
      return video ? this.setVideo(video) : this.addImages(files)
    },
    async setVideo(file) {
      this.error = null
      if (file.size > MAX_VIDEO_SIZE) {
        this.error = 'Das Video ist zu gross (max. 250 MB).'
        return
      }
      const preview = URL.createObjectURL(file)
      const duration = await videoDuration(preview).catch(() => 0)
      if (duration > MAX_VIDEO_DURATION + 0.5) {
        URL.revokeObjectURL(preview)
        this.error = `Das Video ist zu lang (max. ${MAX_VIDEO_DURATION} Sekunden).`
        return
      }
      this.video = { file, preview }
    },
    clearVideo() {
      if (this.video) URL.revokeObjectURL(this.video.preview)
      this.video = null
    },
    async addImages(files) {
      this.error = null
      const free = MAX_IMAGES - this.images.length
      if (files.length > free) this.error = `Du kannst höchstens ${MAX_IMAGES} Bilder hochladen.`
      for (const file of files.slice(0, free)) {
        try {
          const blob = await compressImage(file)
          const size = await imageSize(blob)
          this.images.push({ blob, ...size, preview: URL.createObjectURL(blob) })
        } catch {
          this.error = 'Ein Bild konnte nicht gelesen werden.'
        }
      }
    },
    removeImage(index) {
      URL.revokeObjectURL(this.images[index].preview)
      this.images.splice(index, 1)
    },
    clearImages() {
      for (const image of this.images) URL.revokeObjectURL(image.preview)
      this.images = []
    },
    form() {
      const body = new FormData()
      body.append('text', this.text.trim())
      body.append('visibility', this.visibility)
      if (this.visibility === 'groups') {
        for (const id of this.selectedGroups) body.append('groups', id)
      }
      if (this.kind === 'story') {
        body.append('image', this.storyImage.blob, 'story')
      } else {
        this.images.forEach((image, index) => body.append('images', image.blob, `image-${index}`))
        if (this.video) body.append('video', this.video.file)
      }
      return body
    },
    async submit() {
      if (!this.canSubmit) return
      const story = this.kind === 'story'
      const fallback = story
        ? 'Story konnte nicht erstellt werden.'
        : 'Feed konnte nicht erstellt werden.'
      this.sending = true
      this.error = null
      try {
        await (story ? storiesApi.create(this.form()) : postsApi.create(this.form()))
        this.leave()
      } catch (error) {
        this.error = error.detail ?? fallback
        if (error.status === 429) this.loadQuota()
      } finally {
        this.sending = false
      }
    },
  },
}
</script>

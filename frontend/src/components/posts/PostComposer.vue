<template>
  <BaseDialog ref="dialog" title="Neuer Post">
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
      accept="image/*,video/*"
      label="Bilder oder ein Video hierher ziehen oder klicken"
      multiple
      @select="addMedia"
    />
    <div v-else class="flex gap-2 overflow-x-auto">
      <div
        v-for="(image, index) in images"
        :key="image.preview"
        class="relative h-40 max-w-full shrink-0"
        :style="{ aspectRatio }"
      >
        <img :src="image.preview" alt="" class="size-full object-cover rounded-box bg-base-200" />
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

    <div class="mt-4">
      <VisibilityPicker v-model:visibility="visibility" v-model:groups="selectedGroups" />
    </div>

    <p v-if="error" class="text-error text-sm mt-4">{{ error }}</p>

    <label class="mt-4 flex items-center gap-3 text-sm">
      <input v-model="acceptedTerms" type="checkbox" class="size-8 shrink-0 accent-primary" />
      <span>
        Ich bestätige, dass mein Post den
        <a href="/terms" target="_blank" rel="noopener" class="link text-primary"
          >Nutzungsrichtlinien</a
        >
        entspricht.
      </span>
    </label>
    <p
      v-if="quota"
      class="text-sm mt-4"
      :class="quota.remaining ? 'text-swissfy-muted' : 'text-error'"
    >
      {{
        quota.remaining
          ? `Heute noch ${quota.remaining} von ${quota.limit} Posts möglich.`
          : `Du hast heute bereits ${quota.limit} Posts erstellt.`
      }}
    </p>

    <template #actions>
      <BaseButton :disabled="sending" @click="$refs.dialog.close()">
        <AppIcon name="cross" />
        Abbrechen
      </BaseButton>
      <BaseButton variant="primary" :disabled="!canSubmit" @click="submit">
        <span v-if="sending" class="loading loading-spinner loading-sm"></span>
        <AppIcon v-else name="paper-plane-top" />
        {{ sending ? 'Wird gepostet…' : 'Posten' }}
      </BaseButton>
    </template>
  </BaseDialog>
</template>

<script>
import AppIcon from '@/components/common/AppIcon.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import ImageDropzone from '@/components/common/ImageDropzone.vue'
import VisibilityPicker from '@/components/posts/VisibilityPicker.vue'
import { apiFetch, extractErrorMessage } from '@/lib/api.js'
import { extractHashtags } from '@/lib/hashtags.js'
import { compressImage, imageSize } from '@/lib/image.js'
import { MAX_VIDEO_DURATION, MAX_VIDEO_SIZE, videoDuration } from '@/lib/video.js'
import { useGroupsStore } from '@/stores/posts.js'

const MAX_LENGTH = 500
const MAX_IMAGES = 10

function initialState() {
  return {
    text: '',
    images: [],
    video: null,
    quota: null,
    visibility: 'public',
    selectedGroups: [],
    acceptedTerms: false,
    sending: false,
    error: null,
  }
}

export default {
  name: 'PostComposer',
  components: { AppIcon, BaseButton, BaseDialog, ImageDropzone, VisibilityPicker },
  emits: ['created'],
  data() {
    return {
      ...initialState(),
      maxLength: MAX_LENGTH,
      maxImages: MAX_IMAGES,
    }
  },
  computed: {
    groupsStore() {
      return useGroupsStore()
    },
    hashtags() {
      return extractHashtags(this.text)
    },
    aspectRatio() {
      const [first] = this.images
      return `${first.width} / ${first.height}`
    },
    canSubmit() {
      const hasContent = this.text.trim() !== '' || this.images.length || this.video
      const hasAudience = this.visibility !== 'groups' || this.selectedGroups.length
      const hasQuota = this.quota?.remaining !== 0
      return !this.sending && this.acceptedTerms && hasContent && hasAudience && hasQuota
    },
  },
  methods: {
    open() {
      this.clearImages()
      this.clearVideo()
      Object.assign(this.$data, initialState())
      this.groupsStore.load().catch(() => {})
      this.loadQuota()
      this.$refs.dialog.open()
    },
    async loadQuota() {
      try {
        const response = await apiFetch('/api/posts/quota/')
        if (response.ok) this.quota = await response.json()
      } catch {
        this.quota = null
      }
    },
    addMedia(files) {
      const video = files.find((file) => file.type.startsWith('video/'))
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
    async submit() {
      if (!this.canSubmit) return
      this.sending = true
      this.error = null
      const body = new FormData()
      body.append('text', this.text.trim())
      body.append('visibility', this.visibility)
      if (this.visibility === 'groups') {
        for (const id of this.selectedGroups) body.append('groups', id)
      }
      this.images.forEach((image, index) => body.append('images', image.blob, `image-${index}`))
      if (this.video) body.append('video', this.video.file)
      try {
        const response = await apiFetch('/api/posts/', { method: 'POST', body })
        const data = await response.json().catch(() => null)
        if (!response.ok) {
          this.error = extractErrorMessage(data, 'Post konnte nicht erstellt werden.')
          if (response.status === 429) this.loadQuota()
          return
        }
        this.clearImages()
        this.clearVideo()
        this.$refs.dialog.close()
        this.$emit('created', data)
      } catch {
        this.error = 'Post konnte nicht erstellt werden.'
      } finally {
        this.sending = false
      }
    },
  },
}
</script>

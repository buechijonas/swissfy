<template>
  <BaseCard
    tag="article"
    :inset="!edgeToEdge"
    :class="{ 'max-sm:border-y-0': edgeToEdge, 'cursor-pointer': !detail }"
    @click="open"
  >
    <AuthorHeader :author="post.author">
      <BaseButton
        v-if="folderPicker && saved"
        outline
        shape="square"
        size="sm"
        :disabled="busy"
        title="In Ordner verschieben"
        @click="$refs.folderDialog.open(folder)"
      >
        <AppIcon name="folder" alt="In Ordner verschieben" />
      </BaseButton>
      <BaseButton
        v-if="post.can_report"
        outline
        size="sm"
        :disabled="busy || reported"
        @click="report"
      >
        {{ reported ? 'Gemeldet' : 'Melden' }}
      </BaseButton>
      <DeleteButton
        v-if="post.is_own && !moderation"
        :disabled="busy"
        @click="$refs.confirm.open()"
      />
    </AuthorHeader>

    <p v-if="post.hidden" class="px-4 pt-3 text-xs font-bold text-error">Öffentlich verborgen</p>
    <p v-if="post.text" class="px-4 py-3 whitespace-pre-line break-words">{{ post.text }}</p>

    <div v-if="post.images.length" class="group relative">
      <div
        ref="slides"
        class="flex snap-x snap-mandatory overflow-x-auto [scrollbar-width:none]"
        @scroll.passive="onSlide"
      >
        <component
          :is="detail ? 'div' : 'RouterLink'"
          v-for="src in post.images"
          :key="src"
          :to="postLink"
          class="w-full shrink-0 snap-center"
        >
          <img
            class="w-full object-cover bg-base-200"
            :style="{ aspectRatio: detail ? post.aspect_ratio : post.list_aspect_ratio }"
            :src="src"
            alt=""
            loading="lazy"
          />
        </component>
      </div>
      <template v-if="post.images.length > 1">
        <BaseButton
          v-if="slide > 0"
          variant="neutral"
          shape="circle"
          size="sm"
          class="absolute left-2 top-1/2 -translate-y-1/2 opacity-0 transition-opacity group-hover:opacity-100 max-sm:hidden"
          title="Vorheriges Bild"
          @click="showSlide(slide - 1)"
        >
          <AppIcon name="angle-left" alt="Vorheriges Bild" />
        </BaseButton>
        <BaseButton
          v-if="slide < post.images.length - 1"
          variant="neutral"
          shape="circle"
          size="sm"
          class="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 transition-opacity group-hover:opacity-100 max-sm:hidden"
          title="Nächstes Bild"
          @click="showSlide(slide + 1)"
        >
          <AppIcon name="angle-right" alt="Nächstes Bild" />
        </BaseButton>
        <div class="pointer-events-none absolute inset-x-0 bottom-2 flex justify-center gap-1.5">
          <span
            v-for="(src, index) in post.images"
            :key="src"
            class="size-1.5 rounded-full shadow"
            :class="index === slide ? 'bg-white' : 'bg-white/50'"
          />
        </div>
      </template>
    </div>

    <footer v-if="!moderation" class="flex items-start gap-6 px-4 py-3">
      <div :class="actionClass">
        <button
          type="button"
          :class="triggerClass"
          :disabled="busy"
          title="Gefällt mir"
          @click="toggleLike"
        >
          <AppIcon
            :name="liked ? 'heart-filled' : 'heart'"
            alt="Gefällt mir"
            :class="[iconClass, { 'text-primary': liked }]"
          />
        </button>
        <span :class="labelClass">{{ likeCount }}</span>
      </div>
      <div :class="actionClass">
        <component
          :is="detail ? 'span' : 'RouterLink'"
          :to="detail ? null : postLink"
          :class="triggerClass"
          title="Kommentare"
        >
          <AppIcon name="comment-alt-middle" alt="Kommentare" :class="iconClass" />
        </component>
        <span :class="labelClass">{{ post.comment_count }}</span>
      </div>
      <div class="ml-auto flex flex-col items-end gap-1">
        <button
          type="button"
          :class="triggerClass"
          :disabled="busy"
          :title="saved ? 'Nicht mehr speichern' : 'Speichern'"
          @click="saved ? unsave() : save(null)"
        >
          <AppIcon
            :name="saved ? 'bookmarked' : 'bookmark'"
            :alt="saved ? 'Nicht mehr speichern' : 'Speichern'"
            :class="iconClass"
          />
        </button>
        <span class="text-swissfy-muted" :class="labelClass">
          {{ formatRelativeTime(post.created_at) }}
        </span>
      </div>
    </footer>
    <p v-if="error" class="text-error text-sm px-4 pb-3">{{ error }}</p>

    <ConfirmDialog ref="confirm" message="Willst du diesen Post löschen?" @confirm="remove" />
    <FolderDialog v-if="folderPicker" ref="folderDialog" @select="save" />
  </BaseCard>
</template>

<script>
import { RouterLink } from 'vue-router'
import AppIcon from '@/components/common/AppIcon.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import DeleteButton from '@/components/common/DeleteButton.vue'
import AuthorHeader from '@/components/posts/AuthorHeader.vue'
import FolderDialog from '@/components/posts/FolderDialog.vue'
import { apiFetch } from '@/lib/api.js'
import { formatRelativeTime } from '@/lib/time.js'

export default {
  name: 'PostCard',
  components: {
    RouterLink,
    AppIcon,
    AuthorHeader,
    BaseButton,
    BaseCard,
    ConfirmDialog,
    DeleteButton,
    FolderDialog,
  },
  props: {
    post: { type: Object, required: true },
    detail: { type: Boolean, default: false },
    folderPicker: { type: Boolean, default: false },
    edgeToEdge: { type: Boolean, default: false },
    moderation: { type: Boolean, default: false },
  },
  emits: ['deleted', 'saved-change'],
  data() {
    return {
      liked: this.post.liked,
      likeCount: this.post.like_count,
      saved: this.post.saved,
      reported: this.post.reported,
      folder: this.post.saved_folder,
      slide: 0,
      busy: false,
      error: null,
      actionClass: 'flex flex-col items-center gap-1',
      triggerClass: 'relative flex size-6 box-content p-2.5 -m-2.5 cursor-pointer',
      iconClass: 'size-6!',
      labelClass: 'text-xs leading-4',
    }
  },
  computed: {
    apiBase() {
      return `/api/posts/${this.post.id}`
    },
    postLink() {
      return this.moderation ? `/moderation/posts/${this.post.id}` : `/posts/${this.post.id}`
    },
  },
  methods: {
    formatRelativeTime,
    open(event) {
      if (this.detail || event.target.closest('a, button, dialog, header')) return
      this.$router.push(this.postLink)
    },
    onSlide() {
      const { scrollLeft, clientWidth } = this.$refs.slides
      this.slide = Math.round(scrollLeft / clientWidth)
    },
    showSlide(index) {
      const { slides } = this.$refs
      slides.scrollTo({ left: index * slides.clientWidth, behavior: 'smooth' })
    },
    async request(path, method, body) {
      this.busy = true
      this.error = null
      try {
        const response = await apiFetch(`${this.apiBase}/${path}`, {
          method,
          body: body && JSON.stringify(body),
        })
        if (!response.ok) throw new Error()
        return response
      } catch {
        this.error = 'Aktion fehlgeschlagen.'
        return null
      } finally {
        this.busy = false
      }
    },
    async toggleLike() {
      const response = await this.request('like/', this.liked ? 'DELETE' : 'POST')
      if (!response) return
      const data = await response.json()
      this.liked = data.liked
      this.likeCount = data.like_count
    },
    async save(folder) {
      if (await this.request('save/', 'PUT', { folder })) {
        this.saved = true
        this.folder = folder
        this.$emit('saved-change', { saved: true, folder })
      }
    },
    async unsave() {
      if (await this.request('save/', 'DELETE')) {
        this.saved = false
        this.folder = null
        this.$emit('saved-change', { saved: false, folder: null })
      }
    },
    async report() {
      if (await this.request('report/', 'POST')) this.reported = true
    },
    async remove() {
      if (await this.request('', 'DELETE')) this.$emit('deleted', this.post.id)
    },
  },
}
</script>

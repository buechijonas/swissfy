<template>
  <BaseCard
    tag="article"
    :inset="!edgeToEdge"
    :class="{
      'max-sm:border-y-0': edgeToEdge,
      'cursor-pointer': !detail,
      'relative max-w-full border-0! bg-black!': reel,
      relative: !post.video && !post.images.length,
    }"
    class="touch-manipulation"
    @click="onCardClick"
    @mousedown="preventSelection"
  >
    <div
      :class="{ relative: post.video }"
      @mousemove="showControls"
      @touchstart.passive="showControls"
    >
      <AuthorHeader
        :author="post.author"
        :overlay="Boolean(post.video)"
        :class="{ 'absolute inset-x-0 top-0 z-1': post.video }"
      >
        <template v-if="!reel">
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
            <AppIcon name="flag" />
            {{ reported ? 'Gemeldet' : 'Melden' }}
          </BaseButton>
          <button
            v-if="post.is_own && !moderation"
            type="button"
            :class="triggerClass"
            title="Bearbeiten"
            @click="$refs.edit.open()"
          >
            <AppIcon name="pencil" alt="Bearbeiten" :class="iconClass" />
          </button>
        </template>
      </AuthorHeader>

      <template v-if="!post.video">
        <p v-if="post.hidden" class="px-4 pt-3 text-xs font-bold text-error">
          Öffentlich verborgen
        </p>
        <PostText
          v-if="post.text"
          :text="post.text"
          class="px-4 py-3 whitespace-pre-line break-words"
        />
      </template>

      <div
        v-if="post.video_status === 'processing' || post.video_status === 'failed'"
        class="flex aspect-video items-center justify-center gap-2 bg-base-200 text-sm text-swissfy-muted"
      >
        <AppIcon name="clapperboard-play" />
        {{
          post.video_status === 'failed'
            ? 'Das Video konnte nicht verarbeitet werden.'
            : 'Video wird verarbeitet…'
        }}
      </div>
      <template v-else-if="post.video">
        <video
          ref="video"
          class="post-video block bg-black object-contain"
          :class="
            reel
              ? 'h-[calc(100dvh-var(--reel-chrome-height))] w-auto max-w-full lg:h-[calc(100dvh-48px)]'
              : 'w-full'
          "
          :style="{ aspectRatio: detail ? post.aspect_ratio : post.list_aspect_ratio }"
          :src="`${post.video}#t=0.001`"
          :controls="controlsVisible"
          controlslist="nofullscreen nodownload noplaybackrate noremoteplayback"
          disablepictureinpicture
          disableremoteplayback
          playsinline
          preload="metadata"
          :loop="videoLoop"
          @play="onPlay"
          @pause="onPause"
        ></video>
        <div
          v-if="post.text"
          class="pointer-events-none absolute inset-x-0 bottom-0 bg-linear-to-t from-black/60 to-transparent px-4 pt-8 text-white transition-[padding] [text-shadow:0_1px_2px_rgb(0_0_0/0.6)]"
          :class="[controlsVisible ? 'pb-14' : 'pb-4', { 'pr-16': reel }]"
        >
          <PostText :text="post.text" class="line-clamp-2 break-words" />
        </div>
        <div
          class="absolute inset-x-0 top-0 cursor-pointer"
          :class="controlsVisible ? 'bottom-12' : 'bottom-0'"
          @click.stop="tap(togglePlay)"
        ></div>
        <HeartBurst ref="heart" />
        <Transition name="liquid">
          <button
            v-if="!playing"
            type="button"
            class="app-floating absolute top-1/2 left-1/2 flex size-18 -translate-x-1/2 -translate-y-1/2 cursor-pointer items-center justify-center rounded-full bg-primary text-primary-content shadow-lg transition-transform hover:scale-105"
            title="Abspielen"
            @click="togglePlay"
          >
            <AppIcon name="play" alt="Abspielen" class="ml-1 size-8!" />
          </button>
        </Transition>
      </template>
    </div>
    <p v-if="post.video && post.hidden" class="px-4 pt-3 text-xs font-bold text-error">
      Öffentlich verborgen
    </p>

    <div v-if="post.images.length" class="group relative">
      <HeartBurst ref="heart" />
      <div
        ref="slides"
        class="flex snap-x snap-mandatory overflow-x-auto [scrollbar-width:none]"
        @scroll.passive="onSlide"
      >
        <div v-for="src in post.images" :key="src" class="w-full shrink-0 snap-center">
          <img
            class="w-full object-cover bg-base-200"
            :style="{ aspectRatio: detail ? post.aspect_ratio : post.list_aspect_ratio }"
            :src="src"
            alt=""
            loading="lazy"
          />
        </div>
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

    <HeartBurst v-if="!post.video && !post.images.length" ref="heart" />

    <footer
      v-if="!moderation"
      class="flex"
      :class="
        reel
          ? 'absolute right-3 bottom-28 flex-col items-center gap-5 text-white drop-shadow'
          : 'items-start gap-6 px-4 py-3'
      "
    >
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
        <button
          v-if="hasCommentSheet"
          type="button"
          :class="triggerClass"
          title="Kommentare"
          @click="$refs.comments.open()"
        >
          <AppIcon name="comment-alt-middle" alt="Kommentare" :class="iconClass" />
        </button>
        <span v-else :class="triggerClass" title="Kommentare">
          <AppIcon name="comment-alt-middle" alt="Kommentare" :class="iconClass" />
        </span>
        <span :class="labelClass">{{ commentCount }}</span>
      </div>
      <div :class="actionClass">
        <button
          type="button"
          :class="triggerClass"
          :disabled="busy || post.is_own"
          :title="reposted ? 'Repost entfernen' : 'Reposten'"
          @click="toggleRepost"
        >
          <AppIcon
            name="arrows-retweet"
            :alt="reposted ? 'Repost entfernen' : 'Reposten'"
            :class="[iconClass, { 'text-swissfy-repost': reposted, 'opacity-40': post.is_own }]"
          />
        </button>
        <span class="max-w-20 truncate" :class="labelClass">{{ repostLabel }}</span>
      </div>
      <div class="flex flex-col gap-1" :class="reel ? 'items-center' : 'ml-auto items-end'">
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
        <span v-if="!reel" class="text-swissfy-muted" :class="labelClass">
          {{ formatRelativeTime(post.created_at) }}
        </span>
      </div>
      <button
        v-if="reel && hasMenu"
        type="button"
        :class="triggerClass"
        title="Mehr"
        @click="$refs.menu.open()"
      >
        <AppIcon name="menu-dots-vertical" alt="Mehr" :class="iconClass" />
      </button>
    </footer>
    <p v-if="error" class="text-error text-sm px-4 pb-3">{{ error }}</p>

    <BaseDialog v-if="reel && hasMenu" ref="menu" title="Seed" class="modal-bottom sm:modal-middle">
      <div class="flex flex-col gap-2">
        <BaseButton v-if="post.is_own && !moderation" block @click="editFromMenu">
          <AppIcon name="pencil" />
          Seed bearbeiten
        </BaseButton>
        <BaseButton
          v-if="post.can_report"
          block
          :disabled="busy || reported"
          @click="reportFromMenu"
        >
          <AppIcon name="shield-exclamation" />
          {{ reported ? 'Gemeldet' : 'Seed melden' }}
        </BaseButton>
      </div>
    </BaseDialog>
    <PostEditDialog
      v-if="post.is_own && !moderation"
      ref="edit"
      :post="{ ...post, ...audience }"
      @updated="audience = { visibility: $event.visibility, groups: $event.groups }"
      @deleted="$emit('deleted', post.id)"
    />
    <CommentSheet
      v-if="hasCommentSheet"
      ref="comments"
      :post-id="post.id"
      @created="commentCount += 1"
      @deleted="commentCount = $event.comment_count"
    />
    <FolderDialog v-if="folderPicker" ref="folderDialog" @select="save" />
  </BaseCard>
</template>

<script>
import AppIcon from '@/components/common/AppIcon.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import AuthorHeader from '@/components/posts/AuthorHeader.vue'
import CommentSheet from '@/components/posts/CommentSheet.vue'
import FolderDialog from '@/components/posts/FolderDialog.vue'
import PostEditDialog from '@/components/posts/PostEditDialog.vue'
import HeartBurst from '@/components/posts/HeartBurst.vue'
import PostText from '@/components/posts/PostText.vue'
import { apiFetch } from '@/lib/api.js'
import { formatRelativeTime } from '@/lib/time.js'
import { videoAutoplay, videoLoop } from '@/lib/wellbeing.js'

const DOUBLE_TAP_MS = 250

export default {
  name: 'PostCard',
  components: {
    AppIcon,
    AuthorHeader,
    BaseButton,
    BaseCard,
    BaseDialog,
    CommentSheet,
    FolderDialog,
    HeartBurst,
    PostEditDialog,
    PostText,
  },
  props: {
    post: { type: Object, required: true },
    detail: { type: Boolean, default: false },
    folderPicker: { type: Boolean, default: false },
    edgeToEdge: { type: Boolean, default: false },
    moderation: { type: Boolean, default: false },
    reel: { type: Boolean, default: false },
  },
  emits: ['deleted', 'saved-change'],
  data() {
    return {
      liked: this.post.liked,
      likeCount: this.post.like_count,
      reposted: this.post.reposted,
      reposter: this.post.reposter,
      saved: this.post.saved,
      reported: this.post.reported,
      folder: this.post.saved_folder,
      commentCount: this.post.comment_count,
      audience: { visibility: this.post.visibility, groups: this.post.groups },
      slide: 0,
      playing: false,
      controlsVisible: true,
      busy: false,
      error: null,
      actionClass: 'flex flex-col items-center gap-1',
      triggerClass: 'relative flex size-6 box-content p-2.5 -m-2.5 cursor-pointer',
      iconClass: 'size-6!',
      labelClass: 'text-xs leading-4',
    }
  },
  mounted() {
    if (!this.$refs.video) return
    this.visibilityObserver = new IntersectionObserver(
      ([entry]) => {
        const { video } = this.$refs
        if (!entry.isIntersecting) {
          video.pause()
        } else if (videoAutoplay.value) {
          video.muted = true
          video.play().catch(() => {})
        }
      },
      { threshold: 0.6 },
    )
    this.visibilityObserver.observe(this.$refs.video)
  },
  beforeUnmount() {
    clearTimeout(this.hideControlsTimer)
    clearTimeout(this.tapTimer)
    this.visibilityObserver?.disconnect()
  },
  computed: {
    repostLabel() {
      if (this.reposter) return `@${this.reposter}`
      return this.reposted ? 'Du' : ''
    },
    videoLoop() {
      return videoLoop.value
    },
    hasCommentSheet() {
      return !this.moderation && (this.reel || !this.detail)
    },
    hasMenu() {
      return (this.post.is_own && !this.moderation) || this.post.can_report
    },
    apiBase() {
      return `/api/posts/${this.post.id}`
    },
  },
  methods: {
    formatRelativeTime,
    onCardClick(event) {
      if (event.target.closest('a, button, dialog, header, video')) return
      if (this.moderation) {
        if (!this.detail) this.$router.push(`/moderation/posts/${this.post.id}`)
        return
      }
      this.tap(this.hasCommentSheet && !this.reel ? () => this.$refs.comments.open() : null)
    },
    preventSelection(event) {
      if (event.detail > 1 && !event.target.closest('dialog')) event.preventDefault()
    },
    tap(action) {
      if (this.tapTimer) {
        clearTimeout(this.tapTimer)
        this.tapTimer = null
        if (this.moderation) return
        this.$refs.heart?.show()
        if (!this.liked) this.toggleLike()
        return
      }
      this.tapTimer = setTimeout(() => {
        this.tapTimer = null
        action?.()
      }, DOUBLE_TAP_MS)
    },
    showControls() {
      clearTimeout(this.hideControlsTimer)
      this.controlsVisible = true
      if (this.playing) {
        this.hideControlsTimer = setTimeout(() => (this.controlsVisible = false), 2500)
      }
    },
    onPlay() {
      this.playing = true
      this.showControls()
    },
    onPause() {
      this.playing = false
      this.showControls()
    },
    togglePlay() {
      const { video } = this.$refs
      if (video.paused) video.play()
      else video.pause()
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
    async toggleRepost() {
      const response = await this.request('repost/', this.reposted ? 'DELETE' : 'POST')
      if (!response) return
      const data = await response.json()
      this.reposted = data.reposted
      this.reposter = data.reposter
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
    editFromMenu() {
      this.$refs.menu.close()
      this.$refs.edit.open()
    },
    async reportFromMenu() {
      await this.report()
      this.$refs.menu.close()
    },
    async report() {
      if (await this.request('report/', 'POST')) this.reported = true
    },
  },
}
</script>

<style scoped>
.post-video::-webkit-media-controls-play-button,
.post-video::-webkit-media-controls-overlay-play-button {
  display: none;
}
</style>

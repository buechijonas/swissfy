<template>
  <div
    v-if="unfinished"
    class="flex aspect-video items-center justify-center gap-2 bg-base-200 text-sm text-swissfy-muted"
  >
    <AppIcon name="clapperboard-play" />
    {{ unfinishedText }}
  </div>
  <div v-else class="relative" @click.stop>
    <video
      v-intersect="{ handler: onVisible, threshold: 0.6 }"
      v-playback="requested"
      class="post-video block bg-black object-contain"
      :class="
        reel
          ? 'h-[calc(100dvh-var(--reel-chrome-height))] w-auto max-w-full lg:h-[calc(100dvh-48px)]'
          : 'w-full'
      "
      :style="{ aspectRatio: detail ? post.aspect_ratio : post.list_aspect_ratio }"
      :src="`${post.video}#t=0.001`"
      :controls="controlsVisible"
      :muted="muted"
      controlslist="nofullscreen nodownload noplaybackrate noremoteplayback"
      disablepictureinpicture
      disableremoteplayback
      playsinline
      preload="metadata"
      :loop="loop"
      @play="onPlay"
      @pause="onPause"
    ></video>
    <div
      v-if="overlay && post.text"
      class="pointer-events-none absolute inset-x-0 bottom-0 bg-linear-to-t from-black/60 to-transparent px-4 pt-8 text-white transition-[padding] [text-shadow:0_1px_2px_rgb(0_0_0/0.6)]"
      :class="[controlsVisible ? 'pb-14' : 'pb-4', { 'pr-16': reel }]"
    >
      <PostText :parts="post.text_parts" class="line-clamp-2 break-words" />
    </div>
    <div
      class="absolute inset-x-0 top-0 cursor-pointer"
      :class="controlsVisible ? 'bottom-12' : 'bottom-0'"
      @click="$emit('tap')"
    ></div>
    <slot />
    <Transition name="liquid">
      <button
        v-if="!playing"
        type="button"
        class="app-floating absolute top-1/2 left-1/2 flex size-18 -translate-x-1/2 -translate-y-1/2 cursor-pointer items-center justify-center rounded-full bg-primary text-primary-content shadow-lg transition-transform hover:scale-105"
        title="Abspielen"
        @click="toggle"
      >
        <AppIcon name="play" alt="Abspielen" class="ml-1 size-8!" />
      </button>
    </Transition>
  </div>
</template>

<script>
import { useTimeoutFn } from '@vueuse/core'
import AppIcon from '@core/components/AppIcon.vue'
import PostText from '@/components/posts/PostText.vue'
import intersect from '@/directives/intersect.js'
import playback from '@/directives/playback.js'
import { videoAutoplay, videoLoop } from '@/lib/preferences.js'

const HIDE_CONTROLS_MS = 2500

export default {
  name: 'PostVideo',
  components: { AppIcon, PostText },
  directives: { intersect, playback },
  props: {
    post: { type: Object, required: true },
    detail: { type: Boolean, default: false },
    reel: { type: Boolean, default: false },
    overlay: { type: Boolean, default: false },
  },
  emits: ['tap'],
  data() {
    return {
      requested: false,
      playing: false,
      muted: false,
      controlsVisible: true,
    }
  },
  computed: {
    unfinished() {
      return ['processing', 'failed'].includes(this.post.video_status)
    },
    unfinishedText() {
      if (this.post.video_status === 'failed') return 'Das Video konnte nicht verarbeitet werden.'
      return 'Video wird verarbeitet…'
    },
    loop() {
      return videoLoop.value
    },
  },
  created() {
    this.controlsTimer = useTimeoutFn(this.hideControls, HIDE_CONTROLS_MS, { immediate: false })
  },
  beforeUnmount() {
    this.controlsTimer.stop()
  },
  methods: {
    toggle() {
      this.requested = !this.playing
    },
    onVisible(visible) {
      if (!visible) {
        this.requested = false
        return
      }
      if (!videoAutoplay.value) return
      this.muted = true
      this.requested = true
    },
    onPlay() {
      this.requested = true
      this.playing = true
      this.showControls()
    },
    onPause() {
      this.requested = false
      this.playing = false
      this.showControls()
    },
    showControls() {
      this.controlsVisible = true
      if (this.playing) this.controlsTimer.start()
      else this.controlsTimer.stop()
    },
    hideControls() {
      this.controlsVisible = false
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

<template>
  <Teleport to="body">
    <div
      v-if="current"
      class="fixed inset-0 z-50 flex touch-manipulation select-none flex-col bg-black pb-[env(safe-area-inset-bottom)] text-white"
      role="dialog"
      aria-label="Story"
      @click="tap(next)"
    >
      <div class="absolute inset-x-0 top-0 z-10 flex flex-col gap-3 p-3">
        <div class="flex gap-1">
          <div
            v-for="story in items"
            :key="story.id"
            class="h-0.5 flex-1 overflow-hidden rounded-full bg-white/30"
          >
            <div class="h-full bg-white" :style="{ width: `${barWidth(story)}%` }"></div>
          </div>
        </div>
        <div class="flex items-center gap-3 [text-shadow:0_1px_2px_rgb(0_0_0/0.6)]">
          <UserAvatar class="size-8" :user="author" />
          <span class="truncate text-sm font-bold">@{{ author.username }}</span>
          <span class="text-xs text-white/80">{{ formatRelativeTime(current.created_at) }}</span>
          <button
            type="button"
            class="ml-auto flex cursor-pointer p-2 -m-2"
            title="Schliessen"
            @click.stop="close"
          >
            <AppIcon name="cross" alt="Schliessen" class="size-6!" />
          </button>
        </div>
      </div>

      <div class="relative min-h-0 flex-1">
        <img :src="current.image" alt="Story" class="size-full object-contain" />
        <p
          v-if="current.text"
          class="absolute inset-x-0 bottom-0 whitespace-pre-line bg-black/50 px-4 py-3 text-center"
        >
          {{ current.text }}
        </p>
      </div>
      <button
        v-if="current.is_own"
        type="button"
        class="flex cursor-pointer items-center justify-center gap-2 border-t border-white/20 px-4 py-3"
        title="Gesehen von"
        @click.stop="openViewers"
      >
        <AppIcon name="eyes" alt="Gesehen von" class="size-6!" />
        <span class="text-sm">{{ current.view_count }}</span>
      </button>

      <HeartBurst ref="heart" />

      <div
        class="absolute right-3 bottom-28 flex flex-col items-center gap-5 [text-shadow:0_1px_2px_rgb(0_0_0/0.6)]"
      >
        <div class="flex flex-col items-center gap-1">
          <button
            type="button"
            class="flex cursor-pointer p-2 -m-2"
            :title="current.liked ? 'Gefällt mir nicht mehr' : 'Gefällt mir'"
            :disabled="busy"
            @click.stop="toggleLike"
          >
            <AppIcon
              :name="current.liked ? 'heart-filled' : 'heart'"
              :alt="current.liked ? 'Gefällt mir nicht mehr' : 'Gefällt mir'"
              class="size-6!"
              :class="{ 'text-primary': current.liked }"
            />
          </button>
          <span v-if="current.is_own" class="text-xs leading-4">{{ current.like_count }}</span>
        </div>
        <button
          v-if="current.is_own"
          type="button"
          class="flex cursor-pointer p-2 -m-2"
          title="Mehr"
          @click.stop="openMenu"
        >
          <AppIcon name="menu-dots-vertical" alt="Mehr" class="size-6!" />
        </button>
      </div>
      <p v-if="error" class="absolute inset-x-0 top-24 text-center text-sm text-error">
        {{ error }}
      </p>
    </div>
  </Teleport>
  <BaseDialog
    ref="menu"
    title="Story"
    class="modal-bottom sm:modal-middle"
    @close="menuOpen = false"
  >
    <BaseButton variant="error" outline block :disabled="busy" @click="confirmRemove">
      <AppIcon name="trash" />
      Story löschen
    </BaseButton>
  </BaseDialog>
  <StoryViewersSheet ref="viewers" @close="sheetOpen = false" />
  <ConfirmDialog
    ref="confirm"
    message="Willst du diese Story löschen?"
    @confirm="remove"
    @close="confirmOpen = false"
  />
</template>

<script>
import asyncActionMixin from '@core/mixins/asyncActionMixin.js'
import doubleTapMixin from '@/mixins/doubleTapMixin.js'
import { onKeyStroke, useIntervalFn } from '@vueuse/core'
import clone from 'lodash-es/clone'
import find from 'lodash-es/find'
import forEach from 'lodash-es/forEach'
import head from 'lodash-es/head'
import map from 'lodash-es/map'
import reject from 'lodash-es/reject'
import takeWhile from 'lodash-es/takeWhile'
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import HeartBurst from '@/components/posts/HeartBurst.vue'
import StoryViewersSheet from '@/components/posts/StoryViewersSheet.vue'
import storiesApi from '@/api/stories.js'
import { formatRelativeTime } from '@/lib/time.js'

const DURATION_MS = 5000
const TICK_MS = 50

export default {
  name: 'StoryViewer',
  mixins: [asyncActionMixin, doubleTapMixin],
  components: {
    AppIcon,
    BaseButton,
    BaseDialog,
    ConfirmDialog,
    HeartBurst,
    StoryViewersSheet,
    UserAvatar,
  },
  props: {
    stories: { type: Array, default: () => [] },
    author: { type: Object, required: true },
  },
  emits: ['deleted', 'closed'],
  data() {
    return {
      items: [],
      currentId: null,
      passedIds: [],
      elapsed: 0,
      menuOpen: false,
      confirmOpen: false,
      sheetOpen: false,
      pendingViews: [],
    }
  },
  computed: {
    current() {
      return find(this.items, { id: this.currentId }) ?? null
    },
    upcoming() {
      return find(this.items, (story) => this.isUpcoming(story)) ?? null
    },
    paused() {
      return this.menuOpen || this.confirmOpen || this.sheetOpen
    },
  },
  watch: {
    current(story) {
      if (story && !story.seen) {
        story.seen = true
        this.pendingViews.push(storiesApi.view(story.id).catch(() => {}))
      }
    },
    $route() {
      this.$refs.viewers.close()
      this.close()
    },
  },
  created() {
    this.ticker = useIntervalFn(this.tick, TICK_MS, { immediate: false })
  },
  beforeUnmount() {
    this.close()
  },
  methods: {
    formatRelativeTime,
    open() {
      this.items = map(this.stories, clone)
      const start = find(this.items, { seen: false }) ?? head(this.items)
      this.passedIds = map(
        takeWhile(this.items, (story) => story !== start),
        'id',
      )
      this.currentId = start?.id ?? null
      this.error = null
      this.keyListeners = [onKeyStroke('Escape', this.close), onKeyStroke('ArrowRight', this.next)]
      this.start()
    },
    close() {
      if (this.items.length) {
        Promise.all(this.pendingViews).then(() => this.$emit('closed'))
        this.pendingViews = []
      }
      this.ticker.pause()
      this.tapTimer.stop()
      forEach(this.keyListeners, (stop) => stop())
      this.keyListeners = []
      this.items = []
      this.currentId = null
    },
    start() {
      this.elapsed = 0
      this.ticker.resume()
    },
    tick() {
      if (this.paused) return
      this.elapsed += TICK_MS
      if (this.elapsed >= DURATION_MS) this.next()
    },
    isUpcoming(story) {
      return story.id !== this.currentId && !this.passedIds.includes(story.id)
    },
    next() {
      if (!this.upcoming) {
        this.close()
        return
      }
      this.passedIds.push(this.currentId)
      this.currentId = this.upcoming.id
      this.start()
    },
    barWidth(story) {
      if (this.passedIds.includes(story.id)) return 100
      if (story.id !== this.currentId) return 0
      return Math.min(100, (this.elapsed / DURATION_MS) * 100)
    },
    doubleTap() {
      this.$refs.heart.show()
      if (!this.current.liked) this.toggleLike()
    },
    run(action) {
      return this.runAction(action, 'Aktion fehlgeschlagen.')
    },
    toggleLike() {
      const story = this.current
      return this.run(async () => {
        const data = story.liked
          ? await storiesApi.unlike(story.id)
          : await storiesApi.like(story.id)
        Object.assign(story, data)
      })
    },
    openViewers() {
      this.sheetOpen = true
      this.$refs.viewers.open(this.current.id)
    },
    openMenu() {
      this.menuOpen = true
      this.$refs.menu.open()
    },
    confirmRemove() {
      this.confirmOpen = true
      this.$refs.menu.close()
      this.$refs.confirm.open()
    },
    remove() {
      return this.run(async () => {
        const removed = this.current
        const upcoming = this.upcoming
        await storiesApi.remove(removed.id)
        this.items = reject(this.items, { id: removed.id })
        this.$emit('deleted')
        if (!upcoming) {
          this.close()
          return
        }
        this.currentId = upcoming.id
        this.start()
      })
    },
  },
}
</script>

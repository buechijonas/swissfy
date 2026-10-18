<template>
  <Teleport to="body">
    <div
      v-if="current"
      class="fixed inset-0 z-50 flex touch-manipulation select-none flex-col bg-black pb-[env(safe-area-inset-bottom)] text-white"
      role="dialog"
      aria-label="Story"
      @click="tap"
    >
      <div class="absolute inset-x-0 top-0 z-10 flex flex-col gap-3 p-3">
        <div class="flex gap-1">
          <div
            v-for="(story, position) in items"
            :key="story.id"
            class="h-0.5 flex-1 overflow-hidden rounded-full bg-white/30"
          >
            <div class="h-full bg-white" :style="{ width: `${barWidth(position)}%` }"></div>
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
import AppIcon from '@/components/common/AppIcon.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import HeartBurst from '@/components/posts/HeartBurst.vue'
import StoryViewersSheet from '@/components/posts/StoryViewersSheet.vue'
import { apiFetch } from '@/lib/api.js'
import { formatRelativeTime } from '@/lib/time.js'

const DURATION_MS = 5000
const TICK_MS = 50
const DOUBLE_TAP_MS = 250

export default {
  name: 'StoryViewer',
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
      index: 0,
      elapsed: 0,
      menuOpen: false,
      confirmOpen: false,
      sheetOpen: false,
      pendingViews: [],
      busy: false,
      error: null,
    }
  },
  computed: {
    current() {
      return this.items[this.index] ?? null
    },
  },
  watch: {
    current(story) {
      if (story && !story.seen) {
        story.seen = true
        this.pendingViews.push(
          apiFetch(`/api/stories/${story.id}/view/`, { method: 'POST' }).catch(() => {}),
        )
      }
    },
    $route() {
      this.$refs.viewers.close()
      this.close()
    },
  },
  beforeUnmount() {
    this.close()
  },
  methods: {
    formatRelativeTime,
    open() {
      this.items = this.stories.map((story) => ({ ...story }))
      this.index = Math.max(
        0,
        this.items.findIndex((story) => !story.seen),
      )
      this.error = null
      this.start()
      document.addEventListener('keydown', this.onKeydown)
    },
    close() {
      if (this.items.length) {
        Promise.all(this.pendingViews).then(() => this.$emit('closed'))
        this.pendingViews = []
      }
      clearInterval(this.ticker)
      clearTimeout(this.tapTimer)
      this.tapTimer = null
      this.items = []
      document.removeEventListener('keydown', this.onKeydown)
    },
    start() {
      clearInterval(this.ticker)
      this.elapsed = 0
      this.ticker = setInterval(() => {
        if (this.menuOpen || this.confirmOpen || this.sheetOpen) return
        this.elapsed += TICK_MS
        if (this.elapsed >= DURATION_MS) this.next()
      }, TICK_MS)
    },
    next() {
      if (this.index < this.items.length - 1) {
        this.index++
        this.start()
      } else {
        this.close()
      }
    },
    barWidth(position) {
      if (position < this.index) return 100
      if (position > this.index) return 0
      return Math.min(100, (this.elapsed / DURATION_MS) * 100)
    },
    tap() {
      if (this.tapTimer) {
        clearTimeout(this.tapTimer)
        this.tapTimer = null
        this.$refs.heart.show()
        if (!this.current.liked) this.toggleLike()
        return
      }
      this.tapTimer = setTimeout(() => {
        this.tapTimer = null
        this.next()
      }, DOUBLE_TAP_MS)
    },
    onKeydown(event) {
      if (event.key === 'Escape') this.close()
      if (event.key === 'ArrowRight') this.next()
    },
    async request(path, method) {
      this.busy = true
      this.error = null
      try {
        const response = await apiFetch(`/api/stories/${this.current.id}/${path}`, { method })
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
      const story = this.current
      const response = await this.request('like/', story.liked ? 'DELETE' : 'POST')
      if (response) Object.assign(story, await response.json())
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
    async remove() {
      if (!(await this.request('', 'DELETE'))) return
      this.items.splice(this.index, 1)
      this.$emit('deleted')
      if (this.index >= this.items.length) this.close()
      else this.start()
    },
  },
}
</script>

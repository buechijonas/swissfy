<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div
    ref="list"
    class="flex flex-col pb-8 px-6 max-h-[calc(100dvh-96px)] overflow-y-auto lg:max-h-none lg:overflow-y-visible lg:flex-1"
    @touchstart.passive="swipeStart"
    @touchend="swipeEnd"
    @wheel.passive="wheel"
    @scroll.passive="scrolledAt = Date.now()"
  >
    <div class="mx-auto w-full max-w-150 sm:pt-4">
      <BaseTabs
        class="mb-4"
        :class="{ 'hidden lg:flex': !archiveRevealed }"
        :tabs="tabs"
        :active="activeTab"
      />
      <BaseCard v-if="requests.length && !archive" class="mb-4">
        <h3 class="px-6 pt-4 pb-2 font-bold">Chat-Anfragen</h3>
        <ul class="divide-y divide-swissfy-border">
          <li v-for="user in requests" :key="user.username">
            <UserRow :user="user" :to="chatLink(user)" />
          </li>
        </ul>
      </BaseCard>
      <BaseCard v-if="visibleConversations.length" tag="ul" class="divide-y divide-swissfy-border">
        <li v-for="user in visibleConversations" :key="user.username" class="flex">
          <SwipeRow
            class="flex-1 min-w-0"
            :icon="archiveIcon"
            :label="archiveLabel"
            @action="requestToggle(user)"
          >
            <UserRow :user="user" :to="chatLink(user)">
              <div
                v-if="user.last_message"
                class="contents"
                :class="user.unread ? 'font-bold text-base-content' : 'text-swissfy-muted'"
              >
                <span class="text-xs">
                  {{ formatRelativeTime(user.last_message.created_at, now) }}
                </span>
                <span class="flex items-center gap-1 min-w-0 max-w-full text-sm">
                  <CipherText v-if="previews[user.username] === null" :length="8" />
                  <span v-else class="truncate">{{ previews[user.username] }}</span>
                  <MessageStatus
                    v-if="user.last_message.status"
                    :status="user.last_message.status"
                  />
                </span>
              </div>
            </UserRow>
          </SwipeRow>
          <BaseButton
            variant="ghost"
            shape="square"
            class="hidden lg:inline-flex size-18 rounded-none border-0 border-l border-swissfy-border"
            :title="archiveLabel"
            @click="requestToggle(user)"
          >
            <AppIcon :name="archiveIcon" :alt="archiveLabel" />
          </BaseButton>
        </li>
      </BaseCard>
      <BaseCard v-else-if="conversations" class="p-6">
        <p class="text-swissfy-muted">{{ emptyText }}</p>
      </BaseCard>
      <div v-else class="flex flex-col gap-3">
        <div v-for="n in 3" :key="n" class="flex items-center gap-4 px-6 py-3">
          <div class="skeleton size-12 rounded-full"></div>
          <div class="flex flex-col gap-2">
            <div class="skeleton h-4 w-40"></div>
            <div class="skeleton h-3 w-24"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <ConfirmDialog
    ref="confirmArchive"
    title="Chat archivieren"
    :message="archiveMessage"
    confirm-label="Archivieren"
    confirm-icon="archive"
    confirm-variant="primary"
    @confirm="toggleArchive(pendingArchive)"
  />
  <BaseFooter />
</template>

<script>
import AppIcon from '@/components/common/AppIcon.vue'
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import CipherText from '@/components/common/CipherText.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import BaseTabs from '@/components/common/BaseTabs.vue'
import MessageStatus from '@/components/common/MessageStatus.vue'
import SwipeRow from '@/components/common/SwipeRow.vue'
import UserRow from '@/components/common/UserRow.vue'
import { apiFetch } from '@/lib/api.js'
import { decryptMessage } from '@/lib/chatCrypto.js'
import { localKeys } from '@/lib/chatKeys.js'
import { formatRelativeTime } from '@/lib/time.js'
import { useAuthStore } from '@/stores/auth.js'
import { useChatsStore } from '@/stores/chats.js'

const REFRESH_INTERVAL = 10000
const REVEAL_DISTANCE = 60
const SCROLL_SETTLE = 400

const TABS = [
  { key: 'chats', label: 'Chats' },
  { key: 'archive', label: 'Archiv' },
]

export default {
  name: 'ChatsView',
  components: {
    AppIcon,
    BaseBreadcrumbs,
    BaseButton,
    BaseCard,
    BaseFooter,
    BaseTabs,
    CipherText,
    ConfirmDialog,
    MessageStatus,
    SwipeRow,
    UserRow,
  },
  data() {
    return {
      breadcrumbs: [{ label: 'Chats', to: '/chats' }],
      requests: [],
      conversations: null,
      previews: {},
      now: Date.now(),
      tabs: TABS,
      archiveRevealed: false,
      pendingArchive: null,
    }
  },
  computed: {
    archive() {
      return this.$route.query.tab === 'archive'
    },
    activeTab() {
      return this.archive ? 'archive' : 'chats'
    },
    visibleConversations() {
      return (this.conversations ?? []).filter((user) => user.archived === this.archive)
    },
    archiveIcon() {
      return this.archive ? 'archive-restore' : 'archive'
    },
    archiveLabel() {
      return this.archive ? 'Wiederherstellen' : 'Archivieren'
    },
    archiveMessage() {
      return `Chat mit @${this.pendingArchive?.username} archivieren? Du erhältst für archivierte Chats keine Benachrichtigungen mehr.`
    },
    emptyText() {
      if (this.archive) return 'Keine archivierten Chats.'
      if (this.conversations.length) return 'Alle Chats sind archiviert.'
      return 'Noch keine Chats. Über ein Profil kannst du eine Chat-Anfrage senden.'
    },
  },
  watch: {
    archive: {
      immediate: true,
      handler(archive) {
        if (archive) this.archiveRevealed = true
      },
    },
  },
  async created() {
    this.keys = await localKeys(useAuthStore().user.id)
    await this.load()
    this.refreshTimer = setInterval(() => this.load(), REFRESH_INTERVAL)
    this.clockTimer = setInterval(() => (this.now = Date.now()), 30000)
  },
  beforeUnmount() {
    clearInterval(this.refreshTimer)
    clearInterval(this.clockTimer)
  },
  methods: {
    formatRelativeTime,
    async load() {
      const [requests, conversations] = await Promise.all([
        apiFetch('/api/chats/requests/'),
        apiFetch('/api/chats/conversations/'),
      ])
      if (requests.ok) this.requests = await requests.json()
      const list = conversations.ok ? await conversations.json() : []
      const previews = {}
      await Promise.all(
        list
          .filter((user) => user.last_message)
          .map(async (user) => {
            previews[user.username] = await decryptMessage(user.last_message, this.keys)
          }),
      )
      this.previews = previews
      this.conversations = list
      this.syncUnread()
      this.now = Date.now()
    },
    syncUnread() {
      useChatsStore().unread = this.conversations
        .filter((user) => user.unread && !user.archived)
        .map((user) => user.username)
    },
    requestToggle(user) {
      if (user.archived) return this.toggleArchive(user)
      this.pendingArchive = user
      this.$refs.confirmArchive.open()
    },
    async toggleArchive(user) {
      const archived = !user.archived
      user.archived = archived
      this.syncUnread()
      const response = await apiFetch(`/api/chats/${encodeURIComponent(user.username)}/archive/`, {
        method: archived ? 'POST' : 'DELETE',
      })
      if (!response.ok) {
        user.archived = !archived
        this.syncUnread()
      }
    },
    swipeStart(event) {
      const list = this.$refs.list
      this.swipe = {
        x: event.touches[0].clientX,
        y: event.touches[0].clientY,
        atTop: list.scrollTop <= 0,
      }
    },
    swipeEnd(event) {
      const touch = event.changedTouches[0]
      const dy = touch.clientY - this.swipe.y
      const dx = Math.abs(touch.clientX - this.swipe.x)
      if (this.swipe.atTop && dy > REVEAL_DISTANCE && dy > dx) this.archiveRevealed = true
    },
    wheel(event) {
      const settled = Date.now() - (this.scrolledAt ?? 0) > SCROLL_SETTLE
      if (settled && this.$refs.list.scrollTop <= 0 && event.deltaY < 0) {
        this.archiveRevealed = true
      }
    },
    chatLink(user) {
      return `/chats/${encodeURIComponent(user.username)}`
    },
  },
}
</script>

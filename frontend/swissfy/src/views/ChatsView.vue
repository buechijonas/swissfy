<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div
    class="flex flex-col pb-8 px-6 max-h-[calc(100dvh-var(--mobile-chrome-height))] overflow-y-auto lg:max-h-none lg:overflow-y-visible lg:flex-1"
  >
    <div class="mx-auto w-full max-w-150 sm:pt-4">
      <BaseTabs class="mb-4" :tabs="tabs" :active="activeTab" />
      <ErrorText :message="error" class="mb-4" />
      <BaseCard v-if="requests.length && !archive" class="mb-4">
        <h3 class="px-6 pt-4 pb-2 font-bold">{{ $t('chats.requests') }}</h3>
        <ul class="divide-y divide-app-border">
          <li v-for="user in requests" :key="user.username">
            <UserRow :user="user" :to="chatLink(user)" />
          </li>
        </ul>
      </BaseCard>
      <BaseCard v-if="visibleConversations.length" tag="ul" class="divide-y divide-app-border">
        <li v-for="user in visibleConversations" :key="user.username" class="flex">
          <SwipeRow
            class="flex-1 min-w-0"
            :icon="archiveIcon"
            :label="archiveLabel"
            @action="requestToggle(user)"
          >
            <UserRow :user="user" :to="chatLink(user)">
              <template v-if="user.last_message" #subtitle>
                <span
                  class="flex items-center gap-1 min-w-0 text-sm"
                  :class="user.unread ? 'font-bold text-base-content' : 'text-app-muted'"
                >
                  <CipherText v-if="previews[user.username] === null" :length="8" />
                  <span v-else class="truncate">{{ previews[user.username] }}</span>
                  <MessageStatus
                    v-if="user.last_message.status"
                    :status="user.last_message.status"
                  />
                </span>
              </template>
              <template v-else #subtitle>
                <span class="text-app-muted text-sm truncate">
                  {{ user.pending ? $t('chats.requestSent') : $t('chats.noMessages') }}
                </span>
              </template>
              <span
                v-if="user.last_message"
                class="text-xs"
                :class="user.unread ? 'font-bold text-base-content' : 'text-app-muted'"
              >
                {{ formatRelativeTime(user.last_message.created_at, now) }}
              </span>
            </UserRow>
          </SwipeRow>
          <BaseButton
            variant="ghost"
            shape="square"
            class="hidden lg:inline-flex size-18 rounded-none border-0 border-l border-app-border"
            :title="archiveLabel"
            @click="requestToggle(user)"
          >
            <AppIcon :name="archiveIcon" :alt="archiveLabel" />
          </BaseButton>
        </li>
      </BaseCard>
      <BaseCard v-else-if="conversations" class="p-6">
        <p class="text-app-muted">{{ emptyText }}</p>
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
    :title="$t('chats.archiveTitle')"
    :message="archiveMessage"
    :confirm-label="$t('chats.archive')"
    confirm-icon="archive"
    confirm-variant="primary"
    @confirm="toggleArchive(pendingArchive)"
  />
  <BaseFooter />
</template>

<script>
import clockMixin from '@/mixins/clockMixin.js'
import { mapStores } from 'pinia'
import filter from 'lodash-es/filter'
import map from 'lodash-es/map'
import AppIcon from '@core/components/AppIcon.vue'
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseButton from '@core/components/BaseButton.vue'
import BaseCard from '@core/components/BaseCard.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import ErrorText from '@core/components/ErrorText.vue'
import CipherText from '@/components/common/CipherText.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import BaseTabs from '@/components/common/BaseTabs.vue'
import MessageStatus from '@/components/common/MessageStatus.vue'
import SwipeRow from '@/components/common/SwipeRow.vue'
import UserRow from '@/components/common/UserRow.vue'
import chatsApi from '@/api/chats.js'
import { decryptMessage } from '@/lib/chatCrypto.js'
import { localKeys } from '@/lib/chatKeys.js'
import { formatRelativeTime } from '@/lib/time.js'
import { useAuthStore } from '@/stores/auth.js'
import { useChatsStore } from '@/stores/chats.js'
import { useEventsStore } from '@/stores/events.js'
import { t } from '@/i18n.js'

function chatTabs() {
  return [
    { key: 'chats', label: t('chats.tabChats') },
    { key: 'archive', label: t('chats.tabArchive') },
  ]
}

export default {
  name: 'ChatsView',
  mixins: [clockMixin],
  components: {
    AppIcon,
    BaseBreadcrumbs,
    BaseButton,
    BaseCard,
    BaseFooter,
    BaseTabs,
    CipherText,
    ConfirmDialog,
    ErrorText,
    MessageStatus,
    SwipeRow,
    UserRow,
  },
  data() {
    return {
      requests: [],
      conversations: null,
      previews: {},
      pendingArchive: null,
      error: null,
    }
  },
  computed: {
    tabs() {
      return chatTabs()
    },
    breadcrumbs() {
      return [{ label: t('chats.tabChats'), to: '/chats' }]
    },
    ...mapStores(useAuthStore, useEventsStore),
    archive() {
      return this.$route.query.tab === 'archive'
    },
    activeTab() {
      return this.archive ? 'archive' : 'chats'
    },
    visibleConversations() {
      return filter(this.conversations, { archived: this.archive })
    },
    archiveIcon() {
      return this.archive ? 'archive-restore' : 'archive'
    },
    archiveLabel() {
      return this.archive ? t('chats.restore') : t('chats.archive')
    },
    archiveMessage() {
      return t('chats.archiveMessage', { username: this.pendingArchive?.username })
    },
    emptyText() {
      if (this.archive) return t('chats.noArchived')
      if (this.conversations.length) return t('chats.allArchived')
      return t('chats.empty')
    },
  },
  watch: {
    'eventsStore.chat'() {
      if (this.keys) this.load()
    },
  },
  async created() {
    this.decrypted = {}
    this.keys = await localKeys(this.authStore.user.id)
    await this.load()
  },
  methods: {
    formatRelativeTime,
    async load() {
      try {
        await this.fetchConversations()
        this.error = null
      } catch {
        this.error = t('chats.loadFailed')
      }
    },
    async fetchConversations() {
      const [requests, list] = await Promise.all([chatsApi.requests(), chatsApi.conversations()])
      this.requests = requests
      const previews = {}
      await Promise.all(
        list
          .filter((user) => user.last_message)
          .map(async (user) => {
            previews[user.username] = await this.preview(user.last_message)
          }),
      )
      this.previews = previews
      this.conversations = list
      this.syncUnread()
      this.now = Date.now()
    },
    async preview(message) {
      if (!(message.id in this.decrypted)) {
        this.decrypted[message.id] = (await decryptMessage(message, this.keys)).text
      }
      return this.decrypted[message.id]
    },
    syncUnread() {
      const unread = filter(this.conversations, { unread: true, archived: false })
      useChatsStore().unread = map(unread, 'username')
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
      try {
        await (archived ? chatsApi.archive(user.username) : chatsApi.unarchive(user.username))
      } catch {
        user.archived = !archived
        this.syncUnread()
        this.error = archived ? t('chats.archiveFailed') : t('chats.restoreFailed')
      }
    },
    chatLink(user) {
      return `/chats/${encodeURIComponent(user.username)}`
    },
  },
}
</script>

<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div
    class="flex flex-col pb-8 px-6 max-h-[calc(100dvh-48px)] overflow-y-auto lg:max-h-none lg:overflow-y-visible lg:flex-1"
  >
    <div class="mx-auto w-full max-w-150 sm:pt-4">
      <BaseCard v-if="requests.length" class="mb-4">
        <h3 class="px-6 pt-4 pb-2 font-bold">Chat-Anfragen</h3>
        <ul class="divide-y divide-swissfy-border">
          <li v-for="user in requests" :key="user.username">
            <UserRow :user="user" :to="chatLink(user)" />
          </li>
        </ul>
      </BaseCard>
      <BaseCard v-if="conversations?.length" tag="ul" class="divide-y divide-swissfy-border">
        <li v-for="user in conversations" :key="user.username">
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
                <MessageStatus v-if="user.last_message.status" :status="user.last_message.status" />
              </span>
            </div>
          </UserRow>
        </li>
      </BaseCard>
      <BaseCard v-else-if="conversations" class="p-6">
        <p class="text-swissfy-muted">
          Noch keine Chats. Über ein Profil kannst du eine Chat-Anfrage senden.
        </p>
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
  <BaseFooter />
</template>

<script>
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import CipherText from '@/components/common/CipherText.vue'
import MessageStatus from '@/components/common/MessageStatus.vue'
import UserRow from '@/components/common/UserRow.vue'
import { apiFetch } from '@/lib/api.js'
import { decryptMessage } from '@/lib/chatCrypto.js'
import { localKeys } from '@/lib/chatKeys.js'
import { formatRelativeTime } from '@/lib/time.js'
import { useAuthStore } from '@/stores/auth.js'
import { useChatsStore } from '@/stores/chats.js'

const REFRESH_INTERVAL = 10000

export default {
  name: 'ChatsView',
  components: { BaseBreadcrumbs, BaseCard, BaseFooter, CipherText, MessageStatus, UserRow },
  data() {
    return {
      breadcrumbs: [{ label: 'Chats', to: '/chats' }],
      requests: [],
      conversations: null,
      previews: {},
      now: Date.now(),
    }
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
      useChatsStore().unread = list.filter((user) => user.unread).map((user) => user.username)
      this.now = Date.now()
    },
    chatLink(user) {
      return `/chats/${encodeURIComponent(user.username)}`
    },
  },
}
</script>

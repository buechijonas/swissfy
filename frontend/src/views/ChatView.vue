<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div class="flex flex-col px-6 h-[calc(100dvh-96px)] lg:h-[calc(100dvh-101px)]">
    <div class="mx-auto w-full max-w-150 flex flex-col flex-1 min-h-0">
      <BaseCard v-if="partner" class="sm:mt-4 max-sm:border-t-0 px-4 py-3 flex items-center gap-4">
        <RouterLink :to="profileLink" class="flex items-center gap-4 min-w-0">
          <UserAvatar class="size-12" :user="partner" />
          <div class="flex flex-col min-w-0">
            <span class="flex min-w-0 items-center gap-2">
              <CipherText v-if="!partner.can_view" :length="10" class="font-bold" />
              <span v-else class="font-bold truncate">{{ fullName || partner.username }}</span>
              <RoleBadge :role="partner.role" />
            </span>
            <span class="text-swissfy-muted text-sm truncate">@{{ partner.username }}</span>
          </div>
        </RouterLink>
        <span
          v-if="ready"
          class="ml-auto flex items-center gap-2 text-xs text-swissfy-muted shrink-0"
        >
          <AppIcon name="lock" size="sm" />
          {{ serverKey ? 'Verschlüsselt' : 'Ende-zu-Ende verschlüsselt' }}
        </span>
      </BaseCard>
      <BaseCard
        v-else-if="!error"
        class="sm:mt-4 max-sm:border-t-0 px-4 py-3 flex items-center gap-4"
      >
        <div class="skeleton size-12 rounded-full"></div>
        <div class="flex flex-col gap-2">
          <div class="skeleton h-4 w-40"></div>
          <div class="skeleton h-3 w-24"></div>
        </div>
      </BaseCard>

      <BaseCard
        v-if="error"
        class="p-6 mb-4"
        :class="partner ? 'border-t-0' : 'sm:mt-4 max-sm:border-t-0'"
      >
        <p class="text-swissfy-muted">{{ error }}</p>
      </BaseCard>

      <BaseCard v-else-if="locked" class="p-6 flex flex-col gap-4 border-t-0">
        <p class="text-swissfy-muted">Gib deine Chat-PIN ein, um deine Chats zu entschlüsseln.</p>
        <form class="flex flex-col gap-2" @submit.prevent="unlock">
          <input
            v-model="pin"
            type="password"
            autocomplete="current-password"
            class="input w-full"
            placeholder="Chat-PIN"
          />
          <div class="flex justify-end">
            <BaseButton type="submit" size="sm" variant="primary" :disabled="!pin || unlocking">
              <AppIcon name="unlock" />
              Entsperren
            </BaseButton>
          </div>
        </form>
        <p v-if="pinError" class="text-error text-sm">{{ pinError }}</p>
      </BaseCard>

      <template v-else>
        <BaseCard ref="scroller" class="flex-1 min-h-0 overflow-y-auto p-4 border-t-0">
          <p v-if="ready" class="text-swissfy-muted text-xs text-center mb-4">
            Nachrichten werden nach 14 Tagen automatisch gelöscht.
          </p>
          <div v-if="!ready" class="flex flex-col gap-3">
            <div class="skeleton h-10 w-48"></div>
            <div class="skeleton h-10 w-40 self-end"></div>
          </div>
          <p v-else-if="!messages.length" class="text-swissfy-muted text-center my-8">
            Noch keine Nachrichten.
          </p>
          <div
            v-for="message in messages"
            :key="message.id"
            class="chat"
            :class="message.mine ? 'chat-end' : 'chat-start'"
          >
            <div class="chat-bubble" :class="{ 'chat-bubble-primary': message.mine }">
              <span v-if="message.text !== null" class="whitespace-pre-wrap break-words">
                {{ message.text }}
              </span>
              <span v-else class="italic opacity-70">Auf diesem Gerät nicht lesbar.</span>
            </div>
            <div class="chat-footer mt-1 flex items-center gap-1 text-xs text-swissfy-muted">
              {{ formatRelativeTime(message.createdAt, now) }}
              <MessageStatus v-if="message.mine" :status="message.status" />
            </div>
          </div>
        </BaseCard>

        <div v-if="!ready" class="skeleton h-10 my-4"></div>
        <div
          v-else-if="canRequest && (!chatRequest || declinedByMe)"
          class="my-4 flex justify-center"
        >
          <BaseButton variant="primary" :disabled="answering" @click="updateRequest('', 'POST')">
            Anfrage senden
            <AppIcon name="paper-plane-top" />
          </BaseButton>
        </div>
        <div v-else-if="incomingRequest && confirmDecline" class="my-4 flex justify-center gap-2">
          <BaseButton :disabled="answering" @click="confirmDecline = false">
            <AppIcon name="cross" />
            Abbrechen
          </BaseButton>
          <BaseButton variant="error" :disabled="answering" @click="updateRequest('', 'DELETE')">
            <AppIcon name="cross" />
            Endgültig ablehnen
          </BaseButton>
        </div>
        <div v-else-if="incomingRequest" class="my-4 flex justify-center gap-2">
          <BaseButton :disabled="answering" @click="confirmDecline = true">
            <AppIcon name="cross" />
            Ablehnen
          </BaseButton>
          <BaseButton
            variant="primary"
            :disabled="answering"
            @click="updateRequest('accept/', 'POST')"
          >
            <AppIcon name="check" />
            Annehmen
          </BaseButton>
        </div>
        <div v-else-if="outgoingRequest" class="my-4 flex justify-center">
          <BaseButton :disabled="answering" @click="updateRequest('withdraw/', 'POST')">
            <AppIcon name="cross" />
            Anfrage zurückziehen
          </BaseButton>
        </div>
        <form v-else class="flex items-end gap-2 my-4" @submit.prevent="send">
          <textarea
            v-model="draft"
            rows="1"
            maxlength="2000"
            class="textarea flex-1 min-h-10 resize-none"
            :placeholder="blockedReason || 'Nachricht'"
            :disabled="!ready || Boolean(blockedReason)"
            @keydown.enter.exact.prevent="send"
          ></textarea>
          <BaseButton type="submit" variant="primary" class="min-w-12" :disabled="!canSend">
            <template v-if="cooldown">{{ cooldown }} s</template>
            <AppIcon v-else name="paper-plane-top" alt="Senden" />
          </BaseButton>
        </form>
        <p v-if="sendError" class="text-error text-sm -mt-2 mb-4">{{ sendError }}</p>
      </template>
    </div>
  </div>
  <BaseFooter />
</template>

<script>
import { RouterLink } from 'vue-router'
import AppIcon from '@/components/common/AppIcon.vue'
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import CipherText from '@/components/common/CipherText.vue'
import MessageStatus from '@/components/common/MessageStatus.vue'
import RoleBadge from '@/components/common/RoleBadge.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import { apiFetch, extractErrorMessage } from '@/lib/api.js'
import { decryptMessage, encryptMessage } from '@/lib/chatCrypto.js'
import { localKeys, prepareChatKeys, unlockWithPin } from '@/lib/chatKeys.js'
import { formatRelativeTime } from '@/lib/time.js'
import { useAuthStore } from '@/stores/auth.js'
import { useChatsStore } from '@/stores/chats.js'

const POLL_INTERVAL = 3000

export default {
  name: 'ChatView',
  components: {
    RouterLink,
    AppIcon,
    BaseBreadcrumbs,
    BaseButton,
    BaseCard,
    BaseFooter,
    CipherText,
    MessageStatus,
    RoleBadge,
    UserAvatar,
  },
  data() {
    return {
      partner: null,
      error: null,
      locked: false,
      pinKey: null,
      pin: '',
      pinError: null,
      unlocking: false,
      ready: false,
      keys: [],
      conversationKeys: [],
      serverKey: true,
      messages: [],
      draft: '',
      sending: false,
      sendError: null,
      now: Date.now(),
      cooldown: 0,
      chatRequest: null,
      canRequest: true,
      answering: false,
      confirmDecline: false,
    }
  },
  computed: {
    authStore() {
      return useAuthStore()
    },
    username() {
      return this.$route.params.username
    },
    apiBase() {
      return `/api/chats/${encodeURIComponent(this.username)}`
    },
    breadcrumbs() {
      return [
        { label: 'Chats', to: '/chats' },
        { label: this.username, to: `/chats/${encodeURIComponent(this.username)}` },
      ]
    },
    profileLink() {
      return `/profile/${encodeURIComponent(this.username)}`
    },
    fullName() {
      return [this.partner.first_name, this.partner.last_name].filter(Boolean).join(' ')
    },
    outgoingRequest() {
      return this.chatRequest?.status === 'pending' && !this.chatRequest.incoming
    },
    incomingRequest() {
      return this.chatRequest?.status === 'pending' && this.chatRequest.incoming
    },
    declinedByMe() {
      return this.chatRequest?.status === 'declined' && this.chatRequest.incoming
    },
    blockedReason() {
      const request = this.chatRequest
      if (request?.status === 'declined' && !request.incoming) return 'Anfrage wurde abgelehnt'
      if (!this.canRequest && (!request || this.declinedByMe)) return 'Nimmt keine Chat-Anfragen an'
      return null
    },
    canSend() {
      return (
        this.ready &&
        !this.sending &&
        !this.cooldown &&
        !this.blockedReason &&
        this.draft.trim() !== ''
      )
    },
  },
  watch: {
    username: {
      immediate: true,
      handler() {
        this.init()
      },
    },
  },
  created() {
    this.clockTimer = setInterval(() => (this.now = Date.now()), 30000)
    document.addEventListener('visibilitychange', this.onVisibilityChange)
  },
  beforeUnmount() {
    clearInterval(this.pollTimer)
    clearInterval(this.clockTimer)
    clearInterval(this.cooldownTimer)
    document.removeEventListener('visibilitychange', this.onVisibilityChange)
  },
  methods: {
    async init() {
      clearInterval(this.pollTimer)
      clearInterval(this.cooldownTimer)
      Object.assign(this.$data, this.$options.data.call(this))
      try {
        const response = await apiFetch(
          `/api/social/profiles/${encodeURIComponent(this.username)}/`,
        )
        if (!response.ok) {
          this.error =
            response.status === 404 ? 'Profil nicht gefunden.' : 'Chat konnte nicht geladen werden.'
          return
        }
        this.partner = await response.json()
        if (this.partner.is_self) {
          this.error = 'Mit dir selbst kannst du nicht chatten.'
          return
        }
        const state = await prepareChatKeys(this.authStore.user.id)
        this.locked = state.locked
        this.pinKey = state.pinKey
        if (!this.locked) await this.start()
      } catch (error) {
        this.error = error.message || 'Chat konnte nicht geladen werden.'
      }
    },
    async unlock() {
      this.unlocking = true
      this.pinError = null
      try {
        await unlockWithPin(this.authStore.user.id, this.pinKey, this.pin)
        this.locked = false
        this.pin = ''
        await this.start()
      } catch (error) {
        this.pinError = error.message
      } finally {
        this.unlocking = false
      }
    },
    async start() {
      this.keys = await localKeys(this.authStore.user.id)
      await this.loadConversationKeys()
      this.messages = useChatsStore().cachedMessages(this.username)
      await this.poll()
      this.ready = true
      this.scrollToBottom()
      this.pollTimer = setInterval(() => this.poll(), POLL_INTERVAL)
    },
    async loadConversationKeys() {
      const response = await apiFetch(`${this.apiBase}/keys/`)
      if (!response.ok) throw new Error('Chat konnte nicht geladen werden.')
      const data = await response.json()
      this.conversationKeys = data.keys
      this.serverKey = data.server_key
    },
    onVisibilityChange() {
      if (this.ready && document.visibilityState === 'visible') this.poll()
    },
    async poll() {
      if (this.polling) return
      this.polling = true
      try {
        const lastId = this.messages.at(-1)?.id
        const params = new URLSearchParams()
        if (lastId) params.set('after', lastId)
        if (document.visibilityState === 'visible') params.set('read', 'true')
        const response = await apiFetch(`${this.apiBase}/messages/?${params}`)
        if (!response.ok) return
        const data = await response.json()
        this.chatRequest = data.chat_request
        this.canRequest = data.can_request
        for (const message of this.messages) {
          if (data.statuses[message.id]) message.status = data.statuses[message.id]
        }
        const incoming = await Promise.all(
          data.messages.map(async (message) => ({
            id: message.id,
            mine: message.sender === this.authStore.user.username,
            status: message.status,
            createdAt: message.created_at,
            text: await decryptMessage(message, this.keys),
          })),
        )
        if (params.has('read')) useChatsStore().markRead(this.username)
        if (this.chatRequest?.status === 'accepted') {
          useChatsStore().cacheMessages(this.username, this.messages)
        }
        if (!incoming.length) return
        const scroller = this.$refs.scroller?.$el
        const atBottom =
          !scroller || scroller.scrollHeight - scroller.scrollTop - scroller.clientHeight < 80
        this.messages.push(...incoming)
        if (atBottom || incoming.some((m) => m.mine)) this.scrollToBottom()
      } finally {
        this.polling = false
      }
    },
    async postMessage(text) {
      const payload = await encryptMessage(text, this.conversationKeys, this.serverKey)
      return apiFetch(`${this.apiBase}/messages/`, {
        method: 'POST',
        body: JSON.stringify(payload),
      })
    },
    async send() {
      if (!this.canSend) return
      const text = this.draft.trim()
      this.sending = true
      this.sendError = null
      try {
        let response = await this.postMessage(text)
        if (response.status === 409) {
          await this.loadConversationKeys()
          response = await this.postMessage(text)
        }
        const data = await response.json().catch(() => null)
        if (data?.retry_after) this.startCooldown(data.retry_after)
        if (response.status === 429) return
        if (!response.ok) {
          this.sendError = extractErrorMessage(data, 'Nachricht konnte nicht gesendet werden.')
          if (response.status === 403) await this.poll()
          return
        }
        this.draft = ''
        await this.poll()
      } catch {
        this.sendError = 'Nachricht konnte nicht gesendet werden.'
      } finally {
        this.sending = false
      }
    },
    async updateRequest(path, method) {
      this.answering = true
      this.sendError = null
      try {
        const response = await apiFetch(`${this.apiBase}/request/${path}`, { method })
        const data = await response.json().catch(() => null)
        if (response.ok) {
          this.chatRequest = data
          if (!data) this.messages = []
        } else {
          this.sendError = extractErrorMessage(data, 'Anfrage fehlgeschlagen.')
          await this.poll()
        }
      } finally {
        this.answering = false
        this.confirmDecline = false
      }
    },
    startCooldown(seconds) {
      clearInterval(this.cooldownTimer)
      this.cooldown = seconds
      this.cooldownTimer = setInterval(() => {
        this.cooldown -= 1
        if (this.cooldown <= 0) clearInterval(this.cooldownTimer)
      }, 1000)
    },
    async scrollToBottom() {
      await this.$nextTick()
      const scroller = this.$refs.scroller?.$el
      if (scroller) scroller.scrollTop = scroller.scrollHeight
    },
    formatRelativeTime,
  },
}
</script>

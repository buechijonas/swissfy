<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div
    class="flex flex-col px-6 h-[calc(100dvh-var(--mobile-chrome-height))] lg:h-[calc(100dvh-101px)]"
  >
    <div class="mx-auto w-full max-w-150 flex flex-col flex-1 min-h-0">
      <BaseCard v-if="partner" class="sm:mt-4 max-sm:border-t-0 px-4 py-3 flex items-center gap-4">
        <RouterLink :to="profileLink" class="flex items-center gap-4 min-w-0">
          <UserAvatar class="size-12" :user="partner" />
          <div class="flex flex-col min-w-0">
            <span class="flex min-w-0 items-center gap-2">
              <CipherText v-if="!partner.can_view" :length="10" class="font-bold" />
              <span v-else class="font-bold truncate">{{ partner.display_name }}</span>
              <RoleBadge :role="partner.role" />
            </span>
            <span class="text-app-muted text-sm truncate">@{{ partner.username }}</span>
          </div>
        </RouterLink>
        <span v-if="ready" class="ml-auto flex items-center gap-2 text-xs text-app-muted shrink-0">
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
        <p class="text-app-muted">{{ error }}</p>
      </BaseCard>

      <BaseCard v-else-if="locked" class="p-6 flex flex-col gap-4 border-t-0">
        <p class="text-app-muted">Gib deine Chat-PIN ein, um deine Chats zu entschlüsseln.</p>
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
        <ErrorText :message="pinError" />
      </BaseCard>

      <template v-else>
        <BaseCard
          v-stick-to-bottom="ownMessages"
          class="app-chat flex-1 min-h-0 overflow-y-auto p-4 border-t-0"
        >
          <p v-if="ready" class="text-app-muted text-xs text-center mb-4">
            Nachrichten werden nach 14 Tagen automatisch gelöscht.
          </p>
          <div v-if="!ready" class="flex flex-col gap-3">
            <div class="skeleton h-10 w-48"></div>
            <div class="skeleton h-10 w-40 self-end"></div>
          </div>
          <p v-else-if="!messages.length" class="text-app-muted text-center my-8">
            Noch keine Nachrichten.
          </p>
          <div
            v-for="message in messages"
            :key="message.id"
            class="chat"
            :class="message.isOwn ? 'chat-end' : 'chat-start'"
          >
            <div class="chat-bubble" :class="{ 'chat-bubble-primary': message.isOwn }">
              <span v-if="message.text !== null" class="whitespace-pre-wrap break-words">
                {{ message.text }}
              </span>
              <span v-else class="italic opacity-70">Auf diesem Gerät nicht lesbar.</span>
            </div>
            <div class="chat-footer mt-1 flex items-center gap-1 text-xs text-app-muted">
              {{ formatRelativeTime(message.createdAt, now) }}
              <MessageStatus v-if="message.isOwn" :status="message.status" />
            </div>
          </div>
        </BaseCard>

        <div v-if="!ready" class="skeleton h-10 my-4"></div>
        <div
          v-else-if="canRequest && (!chatRequest || declinedByMe)"
          class="my-4 flex justify-center"
        >
          <BaseButton variant="primary" :disabled="answering" @click="updateRequest('send')">
            Anfrage senden
            <AppIcon name="paper-plane-top" />
          </BaseButton>
        </div>
        <div v-else-if="incomingRequest && confirmDecline" class="my-4 flex justify-center gap-2">
          <BaseButton :disabled="answering" @click="confirmDecline = false">
            <AppIcon name="cross" />
            Abbrechen
          </BaseButton>
          <BaseButton variant="error" :disabled="answering" @click="updateRequest('decline')">
            <AppIcon name="cross" />
            Endgültig ablehnen
          </BaseButton>
        </div>
        <div v-else-if="incomingRequest" class="my-4 flex justify-center gap-2">
          <BaseButton :disabled="answering" @click="confirmDecline = true">
            <AppIcon name="cross" />
            Ablehnen
          </BaseButton>
          <BaseButton variant="primary" :disabled="answering" @click="updateRequest('accept')">
            <AppIcon name="check" />
            Annehmen
          </BaseButton>
        </div>
        <div v-else-if="outgoingRequest" class="my-4 flex justify-center">
          <BaseButton :disabled="answering" @click="updateRequest('withdraw')">
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
        <ErrorText :message="sendError" class="-mt-2 mb-4" />
      </template>
    </div>
  </div>
  <BaseFooter />
</template>

<script>
import ErrorText from '@core/components/ErrorText.vue'
import clockMixin from '@/mixins/clockMixin.js'
import { mapStores } from 'pinia'
import { RouterLink } from 'vue-router'
import { useIntervalFn } from '@vueuse/core'
import some from 'lodash-es/some'
import AppIcon from '@core/components/AppIcon.vue'
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseButton from '@core/components/BaseButton.vue'
import BaseCard from '@core/components/BaseCard.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import CipherText from '@/components/common/CipherText.vue'
import MessageStatus from '@/components/common/MessageStatus.vue'
import RoleBadge from '@/components/common/RoleBadge.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import chatsApi from '@/api/chats.js'
import profilesApi from '@/api/profiles.js'
import { decryptMessage, encryptMessage } from '@/lib/chatCrypto.js'
import stickToBottom from '@/directives/stickToBottom.js'
import { documentVisibility } from '@/lib/browser.js'
import { localKeys, prepareChatKeys, unlockWithPin } from '@/lib/chatKeys.js'
import { formatRelativeTime } from '@/lib/time.js'
import { useAuthStore } from '@/stores/auth.js'
import { useChatsStore } from '@/stores/chats.js'

const POLL_INTERVAL = 3000
const COOLDOWN_STEP = 1000

export default {
  name: 'ChatView',
  mixins: [clockMixin],
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
    ErrorText,
  },
  directives: { stickToBottom },
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
      cooldown: 0,
      chatRequest: null,
      canRequest: true,
      answering: false,
      confirmDecline: false,
      ownMessages: 0,
    }
  },
  computed: {
    ...mapStores(useAuthStore),
    visible() {
      return documentVisibility.value === 'visible'
    },
    username() {
      return this.$route.params.username
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
    visible() {
      if (this.ready && this.visible) this.poll()
    },
    username: {
      immediate: true,
      handler() {
        this.init()
      },
    },
  },
  created() {
    this.poller = useIntervalFn(this.poll, POLL_INTERVAL, { immediate: false })
    this.cooldownTimer = useIntervalFn(this.countDown, COOLDOWN_STEP, { immediate: false })
  },
  beforeUnmount() {
    this.poller.pause()
    this.cooldownTimer.pause()
  },
  methods: {
    async init() {
      this.poller.pause()
      this.cooldownTimer.pause()
      Object.assign(this.$data, this.$options.data.call(this))
      try {
        this.partner = await profilesApi.get(this.username)
        if (this.partner.is_self) {
          this.error = 'Mit dir selbst kannst du nicht chatten.'
          return
        }
        const state = await prepareChatKeys(this.authStore.user.id)
        this.locked = state.locked
        this.pinKey = state.pinKey
        if (!this.locked) await this.start()
      } catch (error) {
        this.error =
          error.status === 404
            ? 'Profil nicht gefunden.'
            : error.detail || error.message || 'Chat konnte nicht geladen werden.'
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
      this.poller.resume()
    },
    async loadConversationKeys() {
      const data = await chatsApi.keys(this.username).catch(() => {
        throw new Error('Chat konnte nicht geladen werden.')
      })
      this.conversationKeys = data.keys
      this.serverKey = data.server_key
    },
    async poll() {
      if (this.polling) return
      this.polling = true
      try {
        const lastId = this.messages.at(-1)?.id
        const read = this.visible
        await chatsApi.receive(this.username, read).catch(() => null)
        const params = lastId ? { after: lastId } : undefined
        const data = await chatsApi.messages(this.username, params).catch(() => null)
        if (!data) return
        this.chatRequest = data.chat_request
        this.canRequest = data.can_request
        for (const message of this.messages) {
          if (data.statuses[message.id]) message.status = data.statuses[message.id]
        }
        const incoming = await Promise.all(
          data.messages.map(async (message) => ({
            id: message.id,
            isOwn: message.is_own,
            status: message.status,
            createdAt: message.created_at,
            text: await decryptMessage(message, this.keys),
          })),
        )
        if (read) useChatsStore().markRead(this.username)
        if (this.chatRequest?.status === 'accepted') {
          useChatsStore().cacheMessages(this.username, this.messages)
        }
        this.messages.push(...incoming)
        if (some(incoming, 'isOwn')) this.ownMessages += 1
      } finally {
        this.polling = false
      }
    },
    async postMessage(text) {
      const payload = await encryptMessage(text, this.conversationKeys, this.serverKey)
      return chatsApi.send(this.username, payload)
    },
    async send() {
      if (!this.canSend) return
      const text = this.draft.trim()
      this.sending = true
      this.sendError = null
      try {
        const data = await this.postMessage(text).catch(async (error) => {
          if (error.status !== 409) throw error
          await this.loadConversationKeys()
          return this.postMessage(text)
        })
        if (data?.retry_after) this.startCooldown(data.retry_after)
        this.draft = ''
        await this.poll()
      } catch (error) {
        if (error.data?.retry_after) this.startCooldown(error.data.retry_after)
        if (error.status === 429) return
        this.sendError = error.detail ?? 'Nachricht konnte nicht gesendet werden.'
        if (error.status === 403) await this.poll()
      } finally {
        this.sending = false
      }
    },
    async updateRequest(action) {
      this.answering = true
      this.sendError = null
      try {
        const data = await chatsApi.updateRequest(this.username, action)
        this.chatRequest = data
        if (!data) this.messages = []
      } catch (error) {
        this.sendError = error.detail ?? 'Anfrage fehlgeschlagen.'
        await this.poll()
      } finally {
        this.answering = false
        this.confirmDecline = false
      }
    },
    startCooldown(seconds) {
      this.cooldown = seconds
      this.cooldownTimer.resume()
    },
    countDown() {
      this.cooldown -= 1
      if (this.cooldown <= 0) this.cooldownTimer.pause()
    },
    formatRelativeTime,
  },
}
</script>

<template>
  <div class="mx-auto w-full max-w-150 flex flex-col flex-1 min-h-0">
    <ChatPartnerCard
      v-if="phase !== 'failed' || partner"
      :partner="partner"
      :encryption="encryption"
      :verifiable="endToEnd"
      @verify="showSafetyNumber = !showSafetyNumber"
    />
    <ChatSafetyNumber
      v-if="endToEnd && (showSafetyNumber || keysChanged)"
      :username="username"
      :groups="safetyGroups"
      :changed="keysChanged"
      @accept="acceptKeys"
    />

    <BaseCard
      v-if="phase === 'failed'"
      class="p-6 mb-4"
      :class="partner ? 'border-t-0' : 'sm:mt-4 max-sm:border-t-0'"
    >
      <p class="text-app-muted">{{ error }}</p>
    </BaseCard>

    <ChatPinUnlock
      v-else-if="phase === 'locked'"
      :user-id="authStore.user.id"
      :pin-key="pinKey"
      @unlocked="start"
    />

    <template v-else>
      <ChatMessageList
        :messages="messages"
        :ready="ready"
        :own-messages="ownMessages"
        :retention-days="retentionDays"
        :verify="endToEnd"
      />
      <p v-if="ready && !eventsStore.connected" class="text-app-muted text-xs text-center mt-2">
        {{ $t('chat.disconnected') }}
      </p>
      <ErrorText :message="refreshError" class="mt-2 text-center" />

      <div v-if="!ready" class="skeleton h-10 my-4"></div>
      <ChatRequestActions
        v-else-if="requestStage"
        :username="username"
        :stage="requestStage"
        @change="changeRequest"
        @fail="refresh"
      />
      <ChatComposer
        v-else
        v-model="draft"
        :blocked-reason="blockedReason"
        :cooldown="cooldown"
        :sending="sending"
        @submit="send"
      />
      <ErrorText :message="sendError" class="-mt-2 mb-4" />
    </template>
  </div>
</template>

<script>
import { mapStores } from 'pinia'
import { useIntervalFn } from '@vueuse/core'
import find from 'lodash-es/find'
import some from 'lodash-es/some'
import unionBy from 'lodash-es/unionBy'
import { toRaw } from 'vue'
import BaseCard from '@core/components/BaseCard.vue'
import ErrorText from '@core/components/ErrorText.vue'
import ChatComposer from '@/components/chats/ChatComposer.vue'
import ChatMessageList from '@/components/chats/ChatMessageList.vue'
import ChatPartnerCard from '@/components/chats/ChatPartnerCard.vue'
import ChatPinUnlock from '@/components/chats/ChatPinUnlock.vue'
import ChatRequestActions from '@/components/chats/ChatRequestActions.vue'
import ChatSafetyNumber from '@/components/chats/ChatSafetyNumber.vue'
import chatsApi from '@/api/chats.js'
import profilesApi from '@/api/profiles.js'
import { documentVisibility } from '@/lib/browser.js'
import { decryptMessage, encryptMessage, safetyNumber, verifyMessage } from '@/lib/chatCrypto.js'
import { localKeys, prepareChatKeys, trustedKeys, trustKeys, unknownKeys } from '@/lib/chatKeys.js'
import { useAuthStore } from '@/stores/auth.js'
import { useChatsStore } from '@/stores/chats.js'
import { useEventsStore } from '@/stores/events.js'
import { t } from '@/i18n.js'

const COOLDOWN_STEP = 1000

export default {
  name: 'ChatConversation',
  components: {
    BaseCard,
    ErrorText,
    ChatComposer,
    ChatMessageList,
    ChatPartnerCard,
    ChatPinUnlock,
    ChatRequestActions,
    ChatSafetyNumber,
  },
  props: {
    username: { type: String, required: true },
  },
  data() {
    return {
      phase: 'loading',
      error: null,
      partner: null,
      pinKey: null,
      keys: [],
      conversationKeys: [],
      verificationKeys: [],
      safetyGroups: [],
      showSafetyNumber: false,
      keysChanged: false,
      serverKey: true,
      retentionDays: null,
      messages: [],
      chatRequest: null,
      canRequest: true,
      refreshing: false,
      refreshError: null,
      draft: '',
      sending: false,
      sendError: null,
      cooldown: 0,
      ownMessages: 0,
    }
  },
  computed: {
    ...mapStores(useAuthStore, useChatsStore, useEventsStore),
    ready() {
      return this.phase === 'ready'
    },
    visible() {
      return documentVisibility.value === 'visible'
    },
    encryption() {
      if (!this.ready) return null
      return this.serverKey ? t('chat.encrypted') : t('chat.endToEnd')
    },
    endToEnd() {
      return this.ready && !this.serverKey
    },
    signer() {
      return (
        find(this.keys, (key) => key.sign && some(this.conversationKeys, { id: key.id })) ?? null
      )
    },
    declinedByMe() {
      return this.chatRequest?.status === 'declined' && this.chatRequest.incoming
    },
    requestStage() {
      const request = this.chatRequest
      if (this.canRequest && (!request || this.declinedByMe)) return 'send'
      if (request?.status !== 'pending') return null
      return request.incoming ? 'incoming' : 'outgoing'
    },
    blockedReason() {
      const request = this.chatRequest
      if (request?.status === 'declined' && !request.incoming) return t('chat.requestDeclined')
      if (!this.canRequest && (!request || this.declinedByMe)) return t('chat.noRequests')
      return null
    },
  },
  watch: {
    'eventsStore.chat'() {
      if (this.ready) this.refresh()
    },
    visible() {
      if (this.ready && this.visible) this.refresh()
    },
  },
  created() {
    this.cooldownTimer = useIntervalFn(this.countDown, COOLDOWN_STEP, { immediate: false })
    this.load()
  },
  beforeUnmount() {
    this.cooldownTimer.pause()
  },
  methods: {
    fail(message) {
      this.error = message
      this.phase = 'failed'
    },
    async load() {
      try {
        this.partner = await profilesApi.get(this.username)
        if (this.partner.is_self) return this.fail(t('chat.self'))
        const state = await prepareChatKeys(this.authStore.user.id)
        this.pinKey = state.pinKey
        if (state.locked) this.phase = 'locked'
        else await this.start()
      } catch (error) {
        this.fail(
          error.status === 404
            ? t('chat.profileNotFound')
            : error.detail || error.message || t('chat.loadFailed'),
        )
      }
    },
    async start() {
      this.phase = 'loading'
      try {
        this.keys = await localKeys(this.authStore.user.id)
        await this.loadConversationKeys()
      } catch (error) {
        return this.fail(error.message)
      }
      this.messages = this.chatsStore.cachedMessages(this.username)
      await this.refresh()
      this.phase = 'ready'
    },
    async loadConversationKeys() {
      const data = await chatsApi.keys(this.username).catch(() => {
        throw new Error(t('chat.loadFailed'))
      })
      await this.checkKeys(data.keys)
      this.conversationKeys = data.keys
      this.serverKey = data.server_key
      this.retentionDays = data.retention_days
      this.safetyGroups = await safetyNumber(data.keys)
    },
    async checkKeys(keys) {
      const userId = this.authStore.user.id
      const trusted = await trustedKeys(userId, this.username)
      if (!trusted) await trustKeys(userId, this.username, keys)
      this.keysChanged = Boolean(trusted) && unknownKeys(trusted, keys, this.username).length > 0
      this.verificationKeys = unionBy(trusted ?? [], keys, 'id')
    },
    async acceptKeys() {
      await trustKeys(this.authStore.user.id, this.username, toRaw(this.conversationKeys))
      this.keysChanged = false
    },
    async refresh() {
      if (this.refreshing) return
      this.refreshing = true
      try {
        await this.receive()
        this.refreshError = null
      } catch {
        this.refreshError = t('chat.refreshFailed')
      } finally {
        this.refreshing = false
      }
    },
    async receive() {
      const read = this.visible
      const data = await chatsApi.receive(this.username, read, this.messages.at(-1)?.id)
      this.chatRequest = data.chat_request
      this.canRequest = data.can_request
      for (const message of this.messages) {
        message.status = data.statuses[message.id] ?? message.status
      }
      const incoming = await Promise.all(data.messages.map(this.decrypt))
      if (read) this.chatsStore.markRead(this.username)
      if (this.chatRequest?.status === 'accepted') {
        this.chatsStore.cacheMessages(this.username, this.messages)
      }
      this.messages.push(...incoming)
      if (some(incoming, 'isOwn')) this.ownMessages += 1
    },
    async decrypt(message) {
      const { text, error } = await decryptMessage(message, this.keys)
      const recipient = message.is_own ? this.username : this.authStore.user.username
      return {
        id: message.id,
        isOwn: message.is_own,
        status: message.status,
        createdAt: message.created_at,
        text,
        error,
        verified: await verifyMessage(message, recipient, this.verificationKeys),
      }
    },
    async postMessage(text) {
      const signer = this.signer && { key: this.signer, recipient: this.username }
      const payload = await encryptMessage(text, this.conversationKeys, this.serverKey, signer)
      return chatsApi.send(this.username, payload)
    },
    async send() {
      const text = this.draft.trim()
      this.sending = true
      this.sendError = null
      try {
        const data = await this.postMessage(text).catch(async (error) => {
          if (error.status !== 409) throw error
          await this.loadConversationKeys()
          return this.postMessage(text)
        })
        this.startCooldown(data.retry_after)
        this.draft = ''
        await this.refresh()
      } catch (error) {
        if (error.data?.retry_after) this.startCooldown(error.data.retry_after)
        if (error.status === 429) return
        this.sendError = error.detail ?? t('chat.sendFailed')
        if (error.status === 403) await this.refresh()
      } finally {
        this.sending = false
      }
    },
    changeRequest(request) {
      this.chatRequest = request
      if (!request) this.messages = []
    },
    startCooldown(seconds) {
      if (!seconds) return
      this.cooldown = seconds
      this.cooldownTimer.resume()
    },
    countDown() {
      this.cooldown -= 1
      if (this.cooldown <= 0) this.cooldownTimer.pause()
    },
  },
}
</script>

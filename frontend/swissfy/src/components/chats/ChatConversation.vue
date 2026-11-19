<template>
  <div class="mx-auto flex min-h-0 w-full max-w-150 flex-1 flex-col">
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
      class="mb-4 p-6"
      :class="partner ? 'border-t-0' : 'max-sm:border-t-0 sm:mt-4'"
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
      <p v-if="ready && !eventsStore.connected" class="mt-2 text-center text-xs text-app-muted">
        {{ $t('chat.disconnected') }}
      </p>
      <ErrorText :message="refreshError" class="mt-2 text-center" />

      <div v-if="!ready" class="my-4 h-10 skeleton"></div>
      <ChatRequestActions
        v-else-if="requestStage"
        :username="username"
        :stage="requestStage"
        @change="changeRequest"
        @fail="refresh"
      />
      <ChatComposer v-else :blocked-reason="blockedReason" :deliver="deliver" />
    </template>
  </div>
</template>

<script>
import find from 'lodash-es/find'
import some from 'lodash-es/some'
import unionBy from 'lodash-es/unionBy'
import { mapStores } from 'pinia'
import { toRaw } from 'vue'
import { ApiError } from '@core/api/client.js'
import BaseCard from '@core/components/BaseCard.vue'
import ErrorText from '@core/components/ErrorText.vue'
import chatsApi from '@/api/chats.js'
import profilesApi from '@/api/profiles.js'
import ChatComposer from '@/components/chats/ChatComposer.vue'
import ChatMessageList from '@/components/chats/ChatMessageList.vue'
import ChatPartnerCard from '@/components/chats/ChatPartnerCard.vue'
import ChatPinUnlock from '@/components/chats/ChatPinUnlock.vue'
import ChatRequestActions from '@/components/chats/ChatRequestActions.vue'
import ChatSafetyNumber from '@/components/chats/ChatSafetyNumber.vue'
import { t } from '@/i18n.js'
import { documentVisibility } from '@/lib/browser.js'
import {
  conversationOf,
  decryptMessage,
  encryptMessage,
  isReplay,
  safetyNumber,
  verifyMessage,
} from '@/lib/chatCrypto.js'
import { localKeys, prepareChatKeys, trustedKeys, trustKeys, unknownKeys } from '@/lib/chatKeys.js'
import { useAuthStore } from '@/stores/auth.js'
import { useChatsStore } from '@/stores/chats.js'
import { useEventsStore } from '@/stores/events.js'

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
      refreshError: null,
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
      if (this.endToEnd && this.keysChanged) return t('chat.confirmKeys')
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
    this.refreshing = null
    this.refreshQueued = false
    this.load()
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
      const unknown = trusted ? await unknownKeys(trusted, keys, this.username) : []
      this.keysChanged = unknown.length > 0
      this.verificationKeys = unionBy(trusted ?? [], keys, 'id')
    },
    async acceptKeys() {
      await trustKeys(this.authStore.user.id, this.username, toRaw(this.conversationKeys))
      this.keysChanged = false
    },
    refresh() {
      if (this.refreshing) {
        this.refreshQueued = true
        return this.refreshing
      }
      this.refreshing = this.receiveUntilCurrent().finally(() => {
        this.refreshing = null
      })
      return this.refreshing
    },
    async receiveUntilCurrent() {
      try {
        do {
          this.refreshQueued = false
          await this.receive()
        } while (this.refreshQueued)
        this.refreshError = null
      } catch {
        this.refreshError = t('chat.refreshFailed')
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
      for (const message of incoming) {
        message.verified = message.verified && !isReplay(message, this.messages)
        this.messages.push(message)
      }
      if (some(incoming, 'isOwn')) this.ownMessages += 1
    },
    async decrypt(message) {
      const conversation = conversationOf(message, this.authStore.user.username, this.username)
      const { text, error, sentAt, nonce } = await decryptMessage(message, this.keys, conversation)
      return {
        id: message.id,
        isOwn: message.is_own,
        status: message.status,
        createdAt: message.created_at,
        text,
        error,
        sentAt,
        nonce,
        verified: await verifyMessage(message, conversation, this.verificationKeys),
      }
    },
    async sendMessage(text) {
      const payload = await encryptMessage(text, this.conversationKeys, {
        conversation: { sender: this.authStore.user.username, recipient: this.username },
        withServerKey: this.serverKey,
        signer: this.signer,
      })
      return chatsApi.send(this.username, payload)
    },
    async deliver(text) {
      const data = await this.sendMessage(text).catch(async (error) => {
        if (error.status === 403) await this.refresh()
        if (error.status !== 409) throw error
        await this.loadConversationKeys()
        if (this.blockedReason) throw new ApiError(409, { detail: this.blockedReason })
        return this.sendMessage(text)
      })
      await this.refresh()
      return data
    },
    changeRequest(request) {
      this.chatRequest = request
      if (!request) this.messages = []
    },
  },
}
</script>

<template>
  <BaseCard
    v-stick-to-bottom="ownMessages"
    class="app-chat flex-1 min-h-0 overflow-y-auto p-4 border-t-0"
  >
    <template v-if="ready">
      <p class="text-app-muted text-xs text-center mb-4">
        {{ $t('chat.retention', { days: retentionDays }) }}
      </p>
      <p v-if="!messages.length" class="text-app-muted text-center my-8">{{ $t('chat.empty') }}</p>
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
          <span v-else-if="message.error === 'invalid'" class="italic opacity-70">
            {{ $t('chat.tampered') }}
          </span>
          <span v-else class="italic opacity-70">{{ $t('chat.unreadable') }}</span>
        </div>
        <div class="chat-footer mt-1 flex items-center gap-1 text-xs text-app-muted">
          {{ formatRelativeTime(message.createdAt, now) }}
          <MessageStatus v-if="message.isOwn" :status="message.status" />
          <span
            v-else-if="verify && message.text !== null && !message.verified"
            class="flex items-center gap-1 text-warning"
          >
            <AppIcon name="shield-exclamation" size="sm" />
            {{ $t('chat.unverified') }}
          </span>
        </div>
      </div>
    </template>
    <div v-else class="flex flex-col gap-3">
      <div class="skeleton h-10 w-48"></div>
      <div class="skeleton h-10 w-40 self-end"></div>
    </div>
  </BaseCard>
</template>

<script>
import AppIcon from '@core/components/AppIcon.vue'
import BaseCard from '@core/components/BaseCard.vue'
import MessageStatus from '@/components/common/MessageStatus.vue'
import stickToBottom from '@/directives/stickToBottom.js'
import { formatRelativeTime } from '@/lib/time.js'
import clockMixin from '@/mixins/clockMixin.js'

export default {
  name: 'ChatMessageList',
  components: { AppIcon, BaseCard, MessageStatus },
  directives: { stickToBottom },
  mixins: [clockMixin],
  props: {
    messages: { type: Array, required: true },
    ready: { type: Boolean, required: true },
    ownMessages: { type: Number, required: true },
    retentionDays: { type: Number, default: null },
    verify: { type: Boolean, default: false },
  },
  methods: {
    formatRelativeTime,
  },
}
</script>

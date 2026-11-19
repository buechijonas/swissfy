<template>
  <BaseCard
    v-stick-to-bottom="ownMessages"
    class="app-chat min-h-0 flex-1 overflow-y-auto border-t-0 p-4"
  >
    <template v-if="ready">
      <p class="mb-4 text-center text-xs text-app-muted">
        {{ $t('chat.retention', { days: retentionDays }) }}
      </p>
      <p v-if="!messages.length" class="my-8 text-center text-app-muted">{{ $t('chat.empty') }}</p>
      <div
        v-for="message in messages"
        :key="message.id"
        class="chat"
        :class="message.isOwn ? 'chat-end' : 'chat-start'"
      >
        <div class="chat-bubble" :class="{ 'chat-bubble-primary': message.isOwn }">
          <span v-if="message.text !== null" class="break-words whitespace-pre-wrap">
            {{ message.text }}
          </span>
          <span v-else-if="message.error === 'invalid'" class="italic opacity-70">
            {{ $t('chat.tampered') }}
          </span>
          <span v-else class="italic opacity-70">{{ $t('chat.unreadable') }}</span>
        </div>
        <div class="chat-footer mt-1 flex items-center gap-1 text-xs text-app-muted">
          {{ formatRelativeTime(message.createdAt, clock.now) }}
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
      <div class="h-10 w-48 skeleton"></div>
      <div class="h-10 w-40 skeleton self-end"></div>
    </div>
  </BaseCard>
</template>

<script>
import AppIcon from '@core/components/AppIcon.vue'
import BaseCard from '@core/components/BaseCard.vue'
import MessageStatus from '@/components/common/MessageStatus.vue'
import { useClock } from '@/composables/clock.js'
import stickToBottom from '@/directives/stickToBottom.js'
import { formatRelativeTime } from '@/lib/time.js'

export default {
  name: 'ChatMessageList',
  components: { AppIcon, BaseCard, MessageStatus },
  directives: { stickToBottom },
  props: {
    messages: { type: Array, required: true },
    ready: { type: Boolean, required: true },
    ownMessages: { type: Number, required: true },
    retentionDays: { type: Number, default: null },
    verify: { type: Boolean, default: false },
  },
  data() {
    return {
      clock: useClock(),
    }
  },
  methods: {
    formatRelativeTime,
  },
}
</script>

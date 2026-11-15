<template>
  <BaseCard class="p-6 flex flex-col gap-4 border-t-0">
    <p class="text-app-muted">{{ $t('chat.enterPin') }}</p>
    <form class="flex flex-col gap-2" @submit.prevent="unlock">
      <input
        v-model="pin"
        type="password"
        autocomplete="current-password"
        class="input w-full"
        :placeholder="$t('chat.pin')"
      />
      <div class="flex justify-end">
        <BaseButton type="submit" size="sm" variant="primary" :disabled="!pin || busy">
          <AppIcon name="unlock" />
          {{ $t('chat.unlock') }}
        </BaseButton>
      </div>
    </form>
    <ErrorText :message="error" />
  </BaseCard>
</template>

<script>
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import BaseCard from '@core/components/BaseCard.vue'
import ErrorText from '@core/components/ErrorText.vue'
import asyncActionMixin from '@core/mixins/asyncActionMixin.js'
import { unlockWithPin } from '@/lib/chatKeys.js'

export default {
  name: 'ChatPinUnlock',
  components: { AppIcon, BaseButton, BaseCard, ErrorText },
  mixins: [asyncActionMixin],
  props: {
    userId: { type: Number, required: true },
    pinKey: { type: Object, required: true },
  },
  emits: ['unlocked'],
  data() {
    return { pin: '' }
  },
  methods: {
    async unlock() {
      await this.runAction(() => unlockWithPin(this.userId, this.pinKey, this.pin))
      if (this.error) return
      this.pin = ''
      this.$emit('unlocked')
    },
  },
}
</script>

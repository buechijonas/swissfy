<template>
  <div class="my-4 flex flex-col items-center gap-2">
    <div v-if="stage === 'send'" class="flex justify-center">
      <BaseButton variant="primary" :disabled="busy" @click="update('send')">
        <AppIcon name="paper-plane-top" />
        {{ $t('chat.sendRequest') }}
      </BaseButton>
    </div>
    <div v-else-if="stage === 'incoming' && confirmDecline" class="flex justify-center gap-2">
      <BaseButton :disabled="busy" @click="confirmDecline = false">
        <AppIcon name="cross" />
        {{ $t('common.cancel') }}
      </BaseButton>
      <BaseButton variant="error" :disabled="busy" @click="update('decline')">
        <AppIcon name="cross" />
        {{ $t('chat.declineForGood') }}
      </BaseButton>
    </div>
    <div v-else-if="stage === 'incoming'" class="flex justify-center gap-2">
      <BaseButton :disabled="busy" @click="confirmDecline = true">
        <AppIcon name="cross" />
        {{ $t('chat.decline') }}
      </BaseButton>
      <BaseButton variant="primary" :disabled="busy" @click="update('accept')">
        <AppIcon name="check" />
        {{ $t('chat.accept') }}
      </BaseButton>
    </div>
    <div v-else class="flex justify-center">
      <BaseButton :disabled="busy" @click="update('withdraw')">
        <AppIcon name="cross" />
        {{ $t('chat.withdraw') }}
      </BaseButton>
    </div>
    <ErrorText :message="error" />
  </div>
</template>

<script>
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import ErrorText from '@core/components/ErrorText.vue'
import asyncActionMixin from '@core/mixins/asyncActionMixin.js'
import chatsApi from '@/api/chats.js'
import { t } from '@/i18n.js'

export default {
  name: 'ChatRequestActions',
  components: { AppIcon, BaseButton, ErrorText },
  mixins: [asyncActionMixin],
  props: {
    username: { type: String, required: true },
    stage: { type: String, required: true },
  },
  emits: ['change', 'fail'],
  data() {
    return { confirmDecline: false }
  },
  methods: {
    async update(action) {
      const request = await this.runAction(
        () => chatsApi.updateRequest(this.username, action),
        t('chat.requestFailed'),
      )
      this.confirmDecline = false
      if (this.error) this.$emit('fail')
      else this.$emit('change', request)
    },
  },
}
</script>

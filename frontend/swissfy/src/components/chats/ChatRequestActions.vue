<template>
  <div class="my-4 flex flex-col items-center gap-2">
    <div v-if="stage === 'send'" class="flex justify-center">
      <BaseButton variant="primary" :disabled="action.busy" @click="update('send')">
        <AppIcon name="paper-plane-top" />
        {{ $t('chat.sendRequest') }}
      </BaseButton>
    </div>
    <div v-else-if="stage === 'incoming' && confirmDecline" class="flex justify-center gap-2">
      <BaseButton :disabled="action.busy" @click="confirmDecline = false">
        <AppIcon name="cross" />
        {{ $t('common.cancel') }}
      </BaseButton>
      <BaseButton variant="error" :disabled="action.busy" @click="update('decline')">
        <AppIcon name="cross" />
        {{ $t('chat.declineForGood') }}
      </BaseButton>
    </div>
    <div v-else-if="stage === 'incoming'" class="flex justify-center gap-2">
      <BaseButton :disabled="action.busy" @click="confirmDecline = true">
        <AppIcon name="cross" />
        {{ $t('chat.decline') }}
      </BaseButton>
      <BaseButton variant="primary" :disabled="action.busy" @click="update('accept')">
        <AppIcon name="check" />
        {{ $t('chat.accept') }}
      </BaseButton>
    </div>
    <div v-else class="flex justify-center">
      <BaseButton :disabled="action.busy" @click="update('withdraw')">
        <AppIcon name="cross" />
        {{ $t('chat.withdraw') }}
      </BaseButton>
    </div>
    <ErrorText :message="action.error" />
  </div>
</template>

<script>
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import ErrorText from '@core/components/ErrorText.vue'
import { useAsyncAction } from '@core/composables/asyncAction.js'
import chatsApi from '@/api/chats.js'
import { t } from '@/i18n.js'

export default {
  name: 'ChatRequestActions',
  components: { AppIcon, BaseButton, ErrorText },
  props: {
    username: { type: String, required: true },
    stage: { type: String, required: true },
  },
  emits: ['change', 'fail'],
  data() {
    return {
      action: useAsyncAction(),
      confirmDecline: false,
    }
  },
  methods: {
    async update(action) {
      const request = await this.action.run(
        () => chatsApi.updateRequest(this.username, action),
        t('chat.requestFailed'),
      )
      this.confirmDecline = false
      if (this.action.error) this.$emit('fail')
      else this.$emit('change', request)
    },
  },
}
</script>

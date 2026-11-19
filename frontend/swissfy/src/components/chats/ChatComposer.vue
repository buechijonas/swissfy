<template>
  <form class="my-4 flex items-end gap-2" @submit.prevent="submit">
    <textarea
      v-model="draft"
      rows="1"
      :maxlength="maxLength"
      class="textarea min-h-10 flex-1 resize-none"
      :placeholder="blockedReason || $t('chat.message')"
      :disabled="Boolean(blockedReason)"
      @keydown.enter.exact.prevent="submit"
    ></textarea>
    <BaseButton type="submit" variant="primary" class="min-w-12" :disabled="!canSend">
      <template v-if="cooldown">{{ cooldown }} s</template>
      <AppIcon v-else name="paper-plane-top" :alt="$t('chat.send')" />
    </BaseButton>
  </form>
  <ErrorText :message="error" class="-mt-2 mb-4" />
</template>

<script>
import { useIntervalFn } from '@vueuse/core'
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import ErrorText from '@core/components/ErrorText.vue'
import { t } from '@/i18n.js'

const MAX_LENGTH = 2000
const COOLDOWN_STEP = 1000

export default {
  name: 'ChatComposer',
  components: { AppIcon, BaseButton, ErrorText },
  props: {
    blockedReason: { type: String, default: null },
    deliver: { type: Function, required: true },
  },
  data() {
    return { draft: '', sending: false, error: null, cooldown: 0, maxLength: MAX_LENGTH }
  },
  computed: {
    canSend() {
      return !this.sending && !this.cooldown && !this.blockedReason && this.draft.trim() !== ''
    },
  },
  created() {
    this.cooldownTimer = useIntervalFn(this.countDown, COOLDOWN_STEP, { immediate: false })
  },
  beforeUnmount() {
    this.cooldownTimer.pause()
  },
  methods: {
    async submit() {
      if (!this.canSend) return
      this.sending = true
      this.error = null
      try {
        const data = await this.deliver(this.draft.trim())
        this.startCooldown(data.retry_after)
        this.draft = ''
      } catch (error) {
        if (error.data?.retry_after) this.startCooldown(error.data.retry_after)
        if (error.status !== 429) this.error = error.detail ?? t('chat.sendFailed')
      } finally {
        this.sending = false
      }
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

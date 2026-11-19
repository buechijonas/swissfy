<template>
  <BaseCard class="flex flex-col gap-4 p-6">
    <div
      class="flex flex-col items-center gap-4 text-center sm:flex-row sm:items-center sm:justify-between sm:text-left"
    >
      <div class="min-w-0">
        <p>{{ $t('chatProtection.title') }}</p>
        <p v-if="mode" class="mt-1 text-sm text-app-muted">{{ chatProtectionHints[mode] }}</p>
      </div>
      <BaseSwitcher
        v-if="mode"
        class="shrink-0 flex-wrap justify-center gap-2"
        size="sm"
        :options="chatProtectionOptions"
        :active="mode"
        :disabled="action.busy"
        @select="select($event)"
      />
      <div v-else-if="!action.error" class="h-8 w-56 skeleton"></div>
    </div>
    <form v-if="pinSetup" class="flex flex-col gap-2" @submit.prevent="save('pin', newPin)">
      <input
        v-model="newPin"
        type="password"
        autocomplete="new-password"
        class="input w-full"
        :placeholder="$t('chatProtection.newPin')"
      />
      <input
        v-model="newPinRepeat"
        type="password"
        autocomplete="new-password"
        class="input w-full"
        :placeholder="$t('chatProtection.repeatPin')"
      />
      <p class="text-sm text-app-muted">
        {{ $t('chatProtection.warning') }}
      </p>
      <div class="flex justify-end gap-2">
        <BaseButton size="sm" :disabled="action.busy" @click="pinSetup = false">
          <AppIcon name="cross" />
          {{ $t('common.cancel') }}
        </BaseButton>
        <BaseButton type="submit" size="sm" variant="primary" :disabled="!pinValid || action.busy">
          <AppIcon name="lock" />
          {{ $t('chatProtection.setPin') }}
        </BaseButton>
      </div>
    </form>
    <ErrorText :message="action.error" class="text-center" />
  </BaseCard>
</template>

<script>
import { mapStores } from 'pinia'
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import BaseCard from '@core/components/BaseCard.vue'
import ErrorText from '@core/components/ErrorText.vue'
import { useAsyncAction } from '@core/composables/asyncAction.js'
import BaseSwitcher from '@/components/common/BaseSwitcher.vue'
import { chatProtectionHints, chatProtectionOptions } from '@/data/settings.js'
import { fetchProtection, setProtection } from '@/lib/chatKeys.js'
import { useAuthStore } from '@/stores/auth.js'

export default {
  name: 'ChatProtectionSetting',
  components: { AppIcon, BaseButton, BaseCard, BaseSwitcher, ErrorText },
  data() {
    return {
      action: useAsyncAction(),
      mode: null,
      pinSetup: false,
      newPin: '',
      newPinRepeat: '',
    }
  },
  computed: {
    ...mapStores(useAuthStore),
    chatProtectionHints,
    chatProtectionOptions,
    pinValid() {
      return this.newPin.length >= 6 && this.newPin === this.newPinRepeat
    },
  },
  async created() {
    try {
      this.mode = (await fetchProtection()).mode
    } catch (error) {
      this.action.error = error.message
    }
  },
  methods: {
    select(mode) {
      this.action.error = null
      if (mode === 'pin') {
        this.pinSetup = true
      } else if (mode !== this.mode) {
        this.pinSetup = false
        this.save(mode)
      }
    },
    async save(mode, pin) {
      const state = await this.action.run(() => setProtection(this.authStore.user.id, mode, pin))
      if (!state) return
      this.mode = state.mode
      this.pinSetup = false
      this.newPin = ''
      this.newPinRepeat = ''
    },
  },
}
</script>

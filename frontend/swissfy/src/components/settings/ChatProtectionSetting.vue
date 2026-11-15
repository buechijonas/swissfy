<template>
  <BaseCard class="p-6 flex flex-col gap-4">
    <div
      class="flex flex-col items-center text-center gap-4 sm:flex-row sm:items-center sm:text-left sm:justify-between"
    >
      <div class="min-w-0">
        <p>{{ $t('chatProtection.title') }}</p>
        <p v-if="mode" class="text-app-muted text-sm mt-1">{{ chatProtectionHints[mode] }}</p>
      </div>
      <BaseSwitcher
        v-if="mode"
        class="flex-wrap justify-center gap-2 shrink-0"
        size="sm"
        :options="chatProtectionOptions"
        :active="mode"
        :disabled="busy"
        @select="select($event)"
      />
      <div v-else-if="!error" class="skeleton h-8 w-56"></div>
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
      <p class="text-app-muted text-sm">
        {{ $t('chatProtection.warning') }}
      </p>
      <div class="flex justify-end gap-2">
        <BaseButton size="sm" :disabled="busy" @click="pinSetup = false">
          <AppIcon name="cross" />
          {{ $t('common.cancel') }}
        </BaseButton>
        <BaseButton type="submit" size="sm" variant="primary" :disabled="!pinValid || busy">
          <AppIcon name="lock" />
          {{ $t('chatProtection.setPin') }}
        </BaseButton>
      </div>
    </form>
    <ErrorText :message="error" class="text-center" />
  </BaseCard>
</template>

<script>
import ErrorText from '@core/components/ErrorText.vue'
import asyncActionMixin from '@core/mixins/asyncActionMixin.js'
import { mapStores } from 'pinia'
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import BaseCard from '@core/components/BaseCard.vue'
import BaseSwitcher from '@/components/common/BaseSwitcher.vue'
import { chatProtectionHints, chatProtectionOptions } from '@/data/settings.js'
import { fetchProtection, setProtection } from '@/lib/chatKeys.js'
import { useAuthStore } from '@/stores/auth.js'

export default {
  name: 'ChatProtectionSetting',
  mixins: [asyncActionMixin],
  components: { AppIcon, BaseButton, BaseCard, BaseSwitcher, ErrorText },
  data() {
    return {
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
      this.error = error.message
    }
  },
  methods: {
    select(mode) {
      this.error = null
      if (mode === 'pin') {
        this.pinSetup = true
      } else if (mode !== this.mode) {
        this.pinSetup = false
        this.save(mode)
      }
    },
    async save(mode, pin) {
      const state = await this.runAction(() => setProtection(this.authStore.user.id, mode, pin))
      if (!state) return
      this.mode = state.mode
      this.pinSetup = false
      this.newPin = ''
      this.newPinRepeat = ''
    },
  },
}
</script>

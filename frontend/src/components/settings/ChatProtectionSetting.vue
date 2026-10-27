<template>
  <BaseCard class="p-6 flex flex-col gap-4">
    <div
      class="flex flex-col items-center text-center gap-4 sm:flex-row sm:items-center sm:text-left sm:justify-between"
    >
      <div class="min-w-0">
        <p>Chat-Verschlüsselung</p>
        <p v-if="mode" class="text-swissfy-muted text-sm mt-1">{{ chatProtectionHints[mode] }}</p>
      </div>
      <BaseSwitcher
        v-if="mode"
        class="flex-wrap justify-center gap-2 shrink-0"
        size="sm"
        :options="chatProtectionOptions"
        :active="mode"
        :disabled="saving"
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
        placeholder="Neue Chat-PIN (mindestens 6 Zeichen)"
      />
      <input
        v-model="newPinRepeat"
        type="password"
        autocomplete="new-password"
        class="input w-full"
        placeholder="Chat-PIN wiederholen"
      />
      <p class="text-swissfy-muted text-sm">
        Ohne PIN kann niemand deine Chats wiederherstellen, auch wir nicht.
      </p>
      <div class="flex justify-end gap-2">
        <BaseButton size="sm" :disabled="saving" @click="pinSetup = false">
          <AppIcon name="cross" />
          Abbrechen
        </BaseButton>
        <BaseButton type="submit" size="sm" variant="primary" :disabled="!pinValid || saving">
          <AppIcon name="lock" />
          PIN festlegen
        </BaseButton>
      </div>
    </form>
    <p v-if="error" class="text-error text-sm text-center">{{ error }}</p>
  </BaseCard>
</template>

<script>
import AppIcon from '@/components/common/AppIcon.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseSwitcher from '@/components/common/BaseSwitcher.vue'
import { chatProtectionHints, chatProtectionOptions } from '@/data/settings.js'
import { fetchProtection, setProtection } from '@/lib/chatKeys.js'
import { useAuthStore } from '@/stores/auth.js'

export default {
  name: 'ChatProtectionSetting',
  components: { AppIcon, BaseButton, BaseCard, BaseSwitcher },
  data() {
    return {
      chatProtectionHints,
      chatProtectionOptions,
      mode: null,
      saving: false,
      error: null,
      pinSetup: false,
      newPin: '',
      newPinRepeat: '',
    }
  },
  computed: {
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
      this.saving = true
      this.error = null
      try {
        this.mode = (await setProtection(useAuthStore().user.id, mode, pin)).mode
        this.pinSetup = false
        this.newPin = ''
        this.newPinRepeat = ''
      } catch (error) {
        this.error = error.message
      } finally {
        this.saving = false
      }
    },
  },
}
</script>

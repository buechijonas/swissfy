<template>
  <div class="mb-10">
    <h3 class="text-xl my-4">Konto</h3>
    <BaseCard
      v-if="authStore.isAuthenticated"
      class="p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
    >
      <div class="min-w-0">
        <p>govex Account Center</p>
        <p class="text-swissfy-muted text-sm mt-1">
          Profil, Profilbild, Passwort und Sicherheit verwaltest du im govex Account Center.
        </p>
      </div>
      <BaseButton class="shrink-0" @click="authStore.openGovexAccount()">
        <AppIcon name="share-square" />
        Zum Account Center
      </BaseButton>
    </BaseCard>
    <BaseCard v-else class="p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div class="min-w-0">
        <p>govex Konto</p>
        <p class="text-swissfy-muted text-sm mt-1">Melde dich mit deinem govex Konto an.</p>
      </div>
      <BaseButton class="shrink-0" @click="authStore.startGovexLogin()">
        <AppIcon name="enter" />
        Anmelden
      </BaseButton>
    </BaseCard>
    <SettingCard
      v-if="authStore.isAuthenticated"
      class="mt-4"
      title="Persistente Anmeldung"
      hint="Wenn an, bleibst du auf diesem Gerät angemeldet, auch wenn Cookies oder der Cache gelöscht werden. Erst wenn alle Websitedaten gelöscht sind, musst du dich neu anmelden."
    >
      <BaseSwitcher
        class="flex-wrap justify-center gap-2 shrink-0"
        size="sm"
        :options="onOffOptions"
        :active="persistentLogin"
        :disabled="saving"
        @select="savePersistentLogin($event)"
      />
    </SettingCard>
    <p v-if="error" class="text-error text-sm mt-4 text-center">{{ error }}</p>
  </div>

  <div class="mb-10">
    <h3 class="text-xl my-4">Rechtliches</h3>
    <div class="flex flex-col gap-4">
      <RouterLink v-for="link in footerLinks" :key="link.to" :to="link.to">
        <BaseCard class="p-6 flex items-center gap-4 hover:bg-swissfy-highlight">
          <AppIcon :name="link.icon" :alt="link.label" class="size-6!" />
          <span>{{ link.label }}</span>
        </BaseCard>
      </RouterLink>
    </div>
  </div>
</template>

<script>
import { RouterLink } from 'vue-router'
import AppIcon from '@/components/common/AppIcon.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseSwitcher from '@/components/common/BaseSwitcher.vue'
import SettingCard from '@/components/settings/SettingCard.vue'
import { footerLinks } from '@/data/footer.js'
import { onOffOptions } from '@/data/settings.js'
import { persistentLogin } from '@/lib/preferences.js'
import { useAuthStore } from '@/stores/auth.js'

export default {
  name: 'GeneralSettings',
  components: { RouterLink, AppIcon, BaseButton, BaseCard, BaseSwitcher, SettingCard },
  data() {
    return { footerLinks, onOffOptions, saving: false, error: null }
  },
  computed: {
    authStore() {
      return useAuthStore()
    },
    persistentLogin() {
      return persistentLogin.value
    },
  },
  methods: {
    async savePersistentLogin(enabled) {
      this.saving = true
      this.error = null
      try {
        await this.authStore.setPersistentLogin(enabled)
      } catch (error) {
        this.error = error.message
      } finally {
        this.saving = false
      }
    },
  },
}
</script>

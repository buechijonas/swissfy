<template>
  <div class="mb-10">
    <h3 class="text-xl my-4">Konto</h3>
    <BaseCard
      v-if="authStore.isAuthenticated"
      class="p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
    >
      <div class="min-w-0">
        <p>govex Account Center</p>
        <p class="text-app-muted text-sm mt-1">
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
        <p class="text-app-muted text-sm mt-1">Melde dich mit deinem govex Konto an.</p>
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
        :disabled="busy"
        @select="savePersistentLogin($event)"
      />
    </SettingCard>
    <ErrorText :message="error" class="mt-4 text-center" />
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
import ErrorText from '@core/components/ErrorText.vue'
import asyncActionMixin from '@core/mixins/asyncActionMixin.js'
import { mapStores } from 'pinia'
import { RouterLink } from 'vue-router'
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import BaseCard from '@core/components/BaseCard.vue'
import BaseSwitcher from '@/components/common/BaseSwitcher.vue'
import SettingCard from '@/components/settings/SettingCard.vue'
import { footerLinks } from '@/data/footer.js'
import { onOffOptions } from '@/data/settings.js'
import { persistentLogin } from '@/lib/preferences.js'
import { useAuthStore } from '@/stores/auth.js'

export default {
  name: 'GeneralSettings',
  mixins: [asyncActionMixin],
  components: { RouterLink, AppIcon, BaseButton, BaseCard, BaseSwitcher, SettingCard, ErrorText },
  data() {
    return { footerLinks, onOffOptions }
  },
  computed: {
    ...mapStores(useAuthStore),
    persistentLogin() {
      return persistentLogin.value
    },
  },
  methods: {
    savePersistentLogin(enabled) {
      return this.runAction(() => this.authStore.setPersistentLogin(enabled))
    },
  },
}
</script>

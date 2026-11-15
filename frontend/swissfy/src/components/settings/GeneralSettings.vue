<template>
  <div class="mb-10">
    <h3 class="text-xl my-4">{{ $t('general.account') }}</h3>
    <BaseCard
      v-if="authStore.isAuthenticated"
      class="p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
    >
      <div class="min-w-0">
        <p>{{ $t('general.accountCenter') }}</p>
        <p class="text-app-muted text-sm mt-1">
          {{ $t('general.accountHint') }}
        </p>
      </div>
      <BaseButton class="shrink-0" @click="authStore.openGovexAccount()">
        <AppIcon name="share-square" />
        {{ $t('general.toAccountCenter') }}
      </BaseButton>
    </BaseCard>
    <BaseCard v-else class="p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div class="min-w-0">
        <p>{{ $t('general.govexAccount') }}</p>
        <p class="text-app-muted text-sm mt-1">{{ $t('general.loginHint') }}</p>
      </div>
      <BaseButton class="shrink-0" @click="authStore.startGovexLogin()">
        <AppIcon name="enter" />
        {{ $t('general.login') }}
      </BaseButton>
    </BaseCard>
    <SettingCard
      v-if="authStore.isAuthenticated"
      class="mt-4"
      :title="$t('general.persistent')"
      :hint="$t('general.persistentHint')"
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
    <h3 class="text-xl my-4">{{ $t('general.legal') }}</h3>
    <div class="flex flex-col gap-4">
      <a v-for="link in footerLinks" :key="link.href" :href="link.href">
        <BaseCard class="p-6 flex items-center gap-4 hover:bg-swissfy-highlight">
          <AppIcon :name="link.icon" :alt="link.label" class="size-6!" />
          <span>{{ link.label }}</span>
        </BaseCard>
      </a>
    </div>
  </div>
</template>

<script>
import ErrorText from '@core/components/ErrorText.vue'
import asyncActionMixin from '@core/mixins/asyncActionMixin.js'
import { mapStores } from 'pinia'
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
  components: { AppIcon, BaseButton, BaseCard, BaseSwitcher, SettingCard, ErrorText },
  computed: {
    ...mapStores(useAuthStore),
    footerLinks,
    onOffOptions,
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

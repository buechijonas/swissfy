<template>
  <div class="mb-10">
    <h3 class="my-4 text-xl">{{ $t('general.account') }}</h3>
    <BaseCard
      v-if="authStore.isAuthenticated"
      class="flex flex-col justify-between gap-4 p-6 sm:flex-row sm:items-center"
    >
      <div class="min-w-0">
        <p>{{ $t('general.accountCenter') }}</p>
        <p class="mt-1 text-sm text-app-muted">
          {{ $t('general.accountHint') }}
        </p>
      </div>
      <BaseButton class="shrink-0" @click="authStore.openGovexAccount()">
        <AppIcon name="share-square" />
        {{ $t('general.toAccountCenter') }}
      </BaseButton>
    </BaseCard>
    <BaseCard v-else class="flex flex-col justify-between gap-4 p-6 sm:flex-row sm:items-center">
      <div class="min-w-0">
        <p>{{ $t('general.govexAccount') }}</p>
        <p class="mt-1 text-sm text-app-muted">{{ $t('general.loginHint') }}</p>
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
        class="shrink-0 flex-wrap justify-center gap-2"
        size="sm"
        :options="onOffOptions"
        :active="persistentLogin"
        :disabled="action.busy"
        @select="savePersistentLogin($event)"
      />
    </SettingCard>
    <ErrorText :message="action.error" class="mt-4 text-center" />
  </div>

  <div class="mb-10">
    <h3 class="my-4 text-xl">{{ $t('general.legal') }}</h3>
    <div class="flex flex-col gap-4">
      <a v-for="link in footerLinks" :key="link.href" :href="link.href">
        <BaseCard class="flex items-center gap-4 p-6 hover:bg-swissfy-highlight">
          <AppIcon :name="link.icon" :alt="link.label" class="size-6!" />
          <span>{{ link.label }}</span>
        </BaseCard>
      </a>
    </div>
  </div>
</template>

<script>
import { mapStores } from 'pinia'
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import BaseCard from '@core/components/BaseCard.vue'
import ErrorText from '@core/components/ErrorText.vue'
import { useAsyncAction } from '@core/composables/asyncAction.js'
import BaseSwitcher from '@/components/common/BaseSwitcher.vue'
import SettingCard from '@/components/settings/SettingCard.vue'
import { footerLinks } from '@/data/footer.js'
import { onOffOptions } from '@/data/settings.js'
import { persistentLogin } from '@/lib/preferences.js'
import { useAuthStore } from '@/stores/auth.js'

export default {
  name: 'GeneralSettings',
  components: { AppIcon, BaseButton, BaseCard, BaseSwitcher, SettingCard, ErrorText },
  data() {
    return {
      action: useAsyncAction(),
    }
  },
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
      return this.action.run(() => this.authStore.setPersistentLogin(enabled))
    },
  },
}
</script>

<template>
  <AuthPage :title="$t('login.title')" :breadcrumb-label="$t('login.title')">
    <p class="mb-6 font-light">
      {{ $t('login.intro') }}
    </p>
    <ErrorText :message="error" class="mb-4" />
    <BaseButton variant="primary" block @click="authStore.startGovexLogin()">
      <AppIcon name="enter" />
      {{ $t('login.button') }}
    </BaseButton>
  </AuthPage>
</template>

<script>
import { mapStores } from 'pinia'
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import ErrorText from '@core/components/ErrorText.vue'
import AuthPage from '@/components/layout/AuthPage.vue'
import { t } from '@/i18n.js'
import { useAuthStore } from '@/stores/auth.js'

function errorMessages() {
  return {
    oidc_failed: t('login.failed'),
  }
}

export default {
  name: 'LoginView',
  components: { AppIcon, AuthPage, BaseButton, ErrorText },
  computed: {
    error() {
      const messages = errorMessages()
      const code = this.$route.query.error ?? ''
      return Object.hasOwn(messages, code) ? messages[code] : ''
    },
    ...mapStores(useAuthStore),
  },
}
</script>

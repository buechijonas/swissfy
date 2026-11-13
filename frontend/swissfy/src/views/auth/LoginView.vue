<template>
  <AuthPage title="Anmelden" breadcrumb-label="Anmelden">
    <p class="font-light mb-6">
      Swissfy nutzt govex für die Anmeldung. Benutzername und Passwort verwaltest du dort.
    </p>
    <ErrorText :message="error" class="mb-4" />
    <BaseButton variant="primary" block @click="authStore.startGovexLogin()">
      <AppIcon name="enter" />
      Mit govex anmelden
    </BaseButton>
  </AuthPage>
</template>

<script>
import ErrorText from '@core/components/ErrorText.vue'
import { mapStores } from 'pinia'
import AuthPage from '@/components/layout/AuthPage.vue'
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import { useAuthStore } from '@/stores/auth.js'

const ERROR_MESSAGES = {
  oidc_failed: 'Die Anmeldung über govex ist fehlgeschlagen. Bitte versuche es erneut.',
}

export default {
  name: 'LoginView',
  components: { AppIcon, AuthPage, BaseButton, ErrorText },
  data() {
    return {
      error: Object.hasOwn(ERROR_MESSAGES, this.$route.query.error ?? '')
        ? ERROR_MESSAGES[this.$route.query.error]
        : '',
    }
  },
  computed: {
    ...mapStores(useAuthStore),
  },
}
</script>

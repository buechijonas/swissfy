<template>
  <AuthPage title="Anmelden" breadcrumb-label="Anmelden">
    <p class="font-light mb-6">
      Swissfy nutzt govex für die Anmeldung. Benutzername und Passwort verwaltest du dort.
    </p>
    <p v-if="error" class="text-error text-sm mb-4">{{ error }}</p>
    <BaseButton variant="primary" block @click="authStore.startGovexLogin()">
      Mit govex anmelden
    </BaseButton>
  </AuthPage>
</template>

<script>
import AuthPage from '@/components/layout/AuthPage.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import { useAuthStore } from '@/stores/auth.js'

const ERROR_MESSAGES = {
  oidc_failed: 'Die Anmeldung über govex ist fehlgeschlagen. Bitte versuche es erneut.',
}

export default {
  name: 'LoginView',
  components: { AuthPage, BaseButton },
  data() {
    return {
      error: Object.hasOwn(ERROR_MESSAGES, this.$route.query.error ?? '')
        ? ERROR_MESSAGES[this.$route.query.error]
        : '',
    }
  },
  computed: {
    authStore() {
      return useAuthStore()
    },
  },
}
</script>

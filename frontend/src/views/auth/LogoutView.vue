<template>
  <AuthPage title="Abmelden" breadcrumb-label="Abmelden">
    <p class="font-light">
      {{ done ? 'Sie wurden erfolgreich abgemeldet.' : 'Sie werden abgemeldet …' }}
    </p>
    <BaseButton variant="primary" block class="mt-6" to="/">
      <AppIcon name="house-blank" />
      Zurück zur Startseite
    </BaseButton>
  </AuthPage>
</template>

<script>
import AuthPage from '@/components/layout/AuthPage.vue'
import AppIcon from '@/components/common/AppIcon.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import { useAuthStore } from '@/stores/auth.js'

export default {
  name: 'LogoutView',
  components: { AppIcon, AuthPage, BaseButton },
  data() {
    return { done: false }
  },
  computed: {
    authStore() {
      return useAuthStore()
    },
  },
  async mounted() {
    try {
      await this.authStore.logout()
    } catch {}
    this.done = true
  },
}
</script>

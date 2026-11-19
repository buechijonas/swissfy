<template>
  <AuthPage :title="$t('logout.title')" :breadcrumb-label="$t('logout.title')">
    <p class="font-light">
      {{ done ? $t('logout.done') : $t('logout.pending') }}
    </p>
    <BaseButton variant="primary" block class="mt-6" to="/">
      <AppIcon name="house-blank" />
      {{ $t('logout.back') }}
    </BaseButton>
  </AuthPage>
</template>

<script>
import { mapStores } from 'pinia'
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import AuthPage from '@/components/layout/AuthPage.vue'
import { useAuthStore } from '@/stores/auth.js'

export default {
  name: 'LogoutView',
  components: { AppIcon, AuthPage, BaseButton },
  data() {
    return { done: false }
  },
  computed: {
    ...mapStores(useAuthStore),
  },
  async mounted() {
    try {
      await this.authStore.logout()
    } catch {}
    this.done = true
  },
}
</script>

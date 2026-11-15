<template>
  <BaseBreadcrumbs :items="[{ label: title, to: $route.path }]" />
  <div
    class="flex flex-col overflow-y-auto max-lg:h-[calc(100dvh-var(--header-height))] lg:max-h-none lg:overflow-y-visible lg:flex-1"
  >
    <LegalArticle :page="page">
      <ErrorText :message="error" />
      <div v-if="pending" class="flex gap-4">
        <BaseButton class="flex-1" to="/logout">
          <AppIcon name="cross" />
          {{ $t('common.cancel') }}
        </BaseButton>
        <BaseButton variant="primary" class="flex-1" :disabled="busy" @click="accept">
          <AppIcon name="check" />
          {{ $t('legal.agree') }}
        </BaseButton>
      </div>
    </LegalArticle>
    <BaseFooter />
  </div>
</template>

<script>
import { mapStores } from 'pinia'
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import ErrorText from '@core/components/ErrorText.vue'
import LegalArticle from '@core/components/LegalArticle.vue'
import { legalTitle } from '@core/legal/index.js'
import asyncActionMixin from '@core/mixins/asyncActionMixin.js'
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import { useAuthStore } from '@/stores/auth.js'

export default {
  name: 'ConsentView',
  components: { AppIcon, BaseBreadcrumbs, BaseButton, BaseFooter, ErrorText, LegalArticle },
  mixins: [asyncActionMixin],
  computed: {
    ...mapStores(useAuthStore),
    page() {
      return this.$route.params.page
    },
    title() {
      return legalTitle(this.page)
    },
    pending() {
      const consent = this.authStore.user?.consent
      return Boolean(consent) && this.page in consent && !consent[this.page]
    },
  },
  methods: {
    async accept() {
      await this.runAction(() => this.authStore.acceptConsent(this.page))
      if (!this.error) this.$router.push('/')
    },
  },
}
</script>

<template>
  <BaseBreadcrumbs :items="[{ label: contract.title, to: `/${page}` }]" />
  <LegalPage>
    <LegalSection
      v-for="(section, index) in contract.sections"
      :key="index"
      :title="section.title"
      :text="section.text"
      :lines="section.lines"
      :items="section.items"
    />
    <div v-if="illustrations[contract.illustration]" class="flex justify-center my-8">
      <img class="max-h-64" :src="illustrations[contract.illustration]" :alt="contract.title" />
    </div>
    <template v-if="pending">
      <p v-if="error" class="text-error text-sm mb-4">{{ error }}</p>
      <BaseButton variant="primary" block :disabled="accepting" @click="onAccept">
        <AppIcon name="check" />
        Zustimmen
      </BaseButton>
    </template>
  </LegalPage>
</template>

<script>
import AppIcon from '@/components/common/AppIcon.vue'
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import LegalPage from '@/components/layout/LegalPage.vue'
import LegalSection from '@/components/legal/LegalSection.vue'
import { contracts, illustrations } from '@/data/legal/index.js'
import { useAuthStore } from '@/stores/auth.js'

export default {
  name: 'LegalContract',
  components: { AppIcon, BaseBreadcrumbs, BaseButton, LegalPage, LegalSection },
  props: {
    page: { type: String, required: true },
  },
  data() {
    return { illustrations, accepting: false, error: '' }
  },
  computed: {
    authStore() {
      return useAuthStore()
    },
    contract() {
      return contracts[this.page]
    },
    pending() {
      const consent = this.authStore.user?.consent
      return Boolean(consent) && this.page in consent && !consent[this.page]
    },
  },
  methods: {
    async onAccept() {
      this.accepting = true
      this.error = ''
      try {
        await this.authStore.acceptConsent(this.page)
        this.$router.push('/')
      } catch (err) {
        this.error = err.message
      } finally {
        this.accepting = false
      }
    },
  },
}
</script>

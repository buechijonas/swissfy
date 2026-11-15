<template>
  <BaseBreadcrumbs :items="[{ label: title }]" />
  <LegalArticle :page="page">
    <template #title>
      <h2 class="truncate text-xl font-light">{{ title }}</h2>
    </template>
  </LegalArticle>
</template>

<script>
import LegalArticle from '@core/components/LegalArticle.vue'
import { legalTitle } from '@core/legal/index.js'
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'

export default {
  name: 'LegalView',
  components: { BaseBreadcrumbs, LegalArticle },
  computed: {
    page() {
      return this.$route.name
    },
    title() {
      return legalTitle(this.page)
    },
  },
}
</script>

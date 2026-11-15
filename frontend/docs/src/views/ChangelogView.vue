<template>
  <DocsPage :breadcrumbs="breadcrumbs" :loading="!changelog" :error="error">
    <ChangelogCard :changelog="changelog" />
  </DocsPage>
</template>

<script>
import ChangelogCard from '@/components/ChangelogCard.vue'
import DocsPage from '@/components/layout/DocsPage.vue'
import asyncActionMixin from '@core/mixins/asyncActionMixin.js'
import { useChangelogsStore } from '@/stores/changelogs.js'
import { t } from '@/i18n.js'

export default {
  name: 'ChangelogView',
  components: { ChangelogCard, DocsPage },
  mixins: [asyncActionMixin],
  data() {
    return {
      changelog: null,
    }
  },
  computed: {
    breadcrumbs() {
      return [
        { label: t('navigation.changelog'), to: '/' },
        { label: `v${this.$route.params.version}` },
      ]
    },
  },
  mounted() {
    this.runAction(async () => {
      this.changelog = await useChangelogsStore().get(this.$route.params.version)
    })
  },
}
</script>

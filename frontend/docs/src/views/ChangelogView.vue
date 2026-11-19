<template>
  <DocsPage :breadcrumbs="breadcrumbs" :loading="!changelog" :error="action.error">
    <ChangelogCard :changelog="changelog" />
  </DocsPage>
</template>

<script>
import { useAsyncAction } from '@core/composables/asyncAction.js'
import ChangelogCard from '@/components/ChangelogCard.vue'
import DocsPage from '@/components/layout/DocsPage.vue'
import { t } from '@/i18n.js'
import { useChangelogsStore } from '@/stores/changelogs.js'

export default {
  name: 'ChangelogView',
  components: { ChangelogCard, DocsPage },
  data() {
    return {
      action: useAsyncAction(),
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
    this.action.run(async () => {
      this.changelog = await useChangelogsStore().get(this.$route.params.version)
    })
  },
}
</script>

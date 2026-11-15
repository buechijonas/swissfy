<template>
  <DocsPage
    :breadcrumbs="[{ label: $t('navigation.changelog') }]"
    :loading="!changelogs"
    :error="error"
  >
    <p v-if="!changelogs.length" class="text-app-muted">{{ $t('changelogs.empty') }}</p>
    <ChangelogCard
      v-for="changelog in changelogs"
      :key="changelog.version"
      :changelog="changelog"
    />
  </DocsPage>
</template>

<script>
import ChangelogCard from '@/components/ChangelogCard.vue'
import DocsPage from '@/components/layout/DocsPage.vue'
import asyncActionMixin from '@core/mixins/asyncActionMixin.js'
import { useChangelogsStore } from '@/stores/changelogs.js'

export default {
  name: 'ChangelogsView',
  components: { ChangelogCard, DocsPage },
  mixins: [asyncActionMixin],
  data() {
    return {
      changelogs: null,
    }
  },
  mounted() {
    this.runAction(async () => {
      this.changelogs = await useChangelogsStore().list()
    })
  },
}
</script>

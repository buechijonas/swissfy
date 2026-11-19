<template>
  <DocsPage
    :breadcrumbs="[{ label: $t('navigation.changelog') }]"
    :loading="!changelogs"
    :error="action.error"
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
import { useAsyncAction } from '@core/composables/asyncAction.js'
import ChangelogCard from '@/components/ChangelogCard.vue'
import DocsPage from '@/components/layout/DocsPage.vue'
import { useChangelogsStore } from '@/stores/changelogs.js'

export default {
  name: 'ChangelogsView',
  components: { ChangelogCard, DocsPage },
  data() {
    return {
      action: useAsyncAction(),
      changelogs: null,
    }
  },
  mounted() {
    this.action.run(async () => {
      this.changelogs = await useChangelogsStore().list()
    })
  },
}
</script>

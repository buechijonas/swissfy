<template>
  <BaseCard tag="article" class="flex max-w-200 flex-col gap-4 rounded-box p-6">
    <header class="flex flex-wrap items-center gap-3">
      <RouterLink :to="`/changelog/${changelog.version}`" class="text-xl font-light">
        v{{ changelog.version }}
      </RouterLink>
      <span class="badge badge-sm" :class="BUMP_BADGES[changelog.bump]">
        {{ BUMP_LABELS[changelog.bump] }}
      </span>
      <time :datetime="changelog.date" class="ml-auto text-sm text-docs-muted">
        {{ formattedDate }}
      </time>
    </header>
    <MarkdownContent :html="changelog.html" />
  </BaseCard>
</template>

<script>
import { RouterLink } from 'vue-router'
import BaseCard from '@/components/common/BaseCard.vue'
import MarkdownContent from '@/components/common/MarkdownContent.vue'

const BUMP_LABELS = { major: 'Major', minor: 'Minor', patch: 'Patch' }
const BUMP_BADGES = { major: 'badge-primary', minor: 'badge-neutral', patch: 'badge-ghost' }
const DATE_FORMAT = new Intl.DateTimeFormat('de-CH', { dateStyle: 'long' })

export default {
  name: 'ChangelogCard',
  components: { RouterLink, BaseCard, MarkdownContent },
  props: {
    changelog: { type: Object, required: true },
  },
  data() {
    return { BUMP_LABELS, BUMP_BADGES }
  },
  computed: {
    formattedDate() {
      return DATE_FORMAT.format(new Date(this.changelog.date))
    },
  },
}
</script>

<template>
  <article class="mx-auto flex w-full max-w-200 flex-1 flex-col gap-12 px-6 pt-4 pb-16">
    <h1 class="font-display text-5xl font-bold tracking-tighter">{{ title }}</h1>
    <div class="flex max-w-150 flex-col gap-10">
      <template v-if="contract">
        <p v-if="contract.notice" class="text-app-muted italic">{{ contract.notice }}</p>
        <LegalSection
          v-for="section in contract.sections"
          :key="section.title ?? section.lines?.[0]"
          :title="section.title"
          :text="section.text"
          :lines="section.lines"
          :items="section.items"
        />
        <div v-if="illustration" class="flex">
          <img class="max-h-64" :src="illustration" :alt="title" />
        </div>
      </template>
      <slot />
    </div>
  </article>
</template>

<script>
import LegalSection from '@core/components/LegalSection.vue'
import { illustrations, legalTitle, loadContract } from '@core/legal/index.js'
import { language } from '@core/lib/language.js'

export default {
  name: 'LegalArticle',
  components: { LegalSection },
  props: {
    page: { type: String, required: true },
  },
  data() {
    return { contract: null }
  },
  computed: {
    title() {
      return legalTitle(this.page)
    },
    source() {
      return `${language.value}:${this.page}`
    },
    illustration() {
      return illustrations[this.contract?.illustration]
    },
  },
  watch: {
    source: { handler: 'load', immediate: true },
  },
  methods: {
    async load() {
      const source = this.source
      const contract = await loadContract(this.page)
      if (source === this.source) this.contract = contract
    },
  },
}
</script>

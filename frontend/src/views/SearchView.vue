<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div
    class="flex flex-col pb-8 px-6 max-h-[calc(100dvh-101px)] overflow-y-auto lg:max-h-none lg:overflow-y-visible lg:flex-1"
  >
    <div class="mx-auto w-full max-w-150">
      <h2 class="text-xl font-light my-4">Suchen</h2>
      <BaseCard class="p-6">
        <p class="text-swissfy-muted">Die Suche ist noch in Arbeit.</p>
      </BaseCard>
    </div>
  </div>
  <BaseFooter />
</template>

<script>
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'

export default {
  name: 'SearchView',
  components: { BaseBreadcrumbs, BaseCard, BaseFooter },
  data() {
    return {
      breadcrumbs: [{ label: 'Suchen', to: '/search' }],
    }
  },
}
</script>

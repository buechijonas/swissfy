<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div
    class="flex flex-col pb-8 px-6 max-h-[calc(100dvh-48px)] overflow-y-auto lg:max-h-none lg:overflow-y-visible lg:flex-1"
  >
    <div class="mx-auto w-full max-w-150 sm:pt-4">
      <BaseCard class="p-6">
        <p class="text-swissfy-muted">Gespeicherte Inhalte sind noch in Arbeit.</p>
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
  name: 'SavedView',
  components: { BaseBreadcrumbs, BaseCard, BaseFooter },
  data() {
    return {
      breadcrumbs: [{ label: 'Gespeichert', to: '/saved' }],
    }
  },
}
</script>

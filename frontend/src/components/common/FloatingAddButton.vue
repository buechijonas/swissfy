<template>
  <BaseButton
    v-if="action"
    variant="primary"
    shape="circle"
    :title="action.label"
    :aria-busy="action.loading"
    class="fixed bottom-[calc(var(--footer-height)+1.5rem)] right-6 z-10 size-14 lg:hidden"
    @click="!action.loading && action.onClick()"
  >
    <span v-if="action.loading" class="loading loading-spinner"></span>
    <AppIcon v-else :name="action.icon" :alt="action.label" class="size-6!" />
  </BaseButton>
</template>

<script>
import AppIcon from '@/components/common/AppIcon.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import { useAddButtonStore } from '@/stores/addButton.js'

export default {
  name: 'FloatingAddButton',
  components: { AppIcon, BaseButton },
  computed: {
    action() {
      return useAddButtonStore().action
    },
  },
}
</script>

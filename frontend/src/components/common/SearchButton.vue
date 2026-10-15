<template>
  <Teleport to="body">
    <BaseButton
      variant="primary"
      shape="circle"
      title="Suchen"
      class="fixed bottom-[calc(var(--footer-height)+1.5rem)] right-6 z-10 size-14 lg:hidden"
      @click="$emit('click')"
    >
      <AppIcon name="search" alt="Suchen" class="size-6!" />
    </BaseButton>
  </Teleport>
</template>

<script>
import AppIcon from '@/components/common/AppIcon.vue'
import BaseButton from '@/components/common/BaseButton.vue'

export default {
  name: 'SearchButton',
  components: { AppIcon, BaseButton },
  emits: ['click'],
}
</script>

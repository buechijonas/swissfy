<template>
  <BaseButton
    variant="primary"
    size="sm"
    class="hidden lg:inline-flex -my-1.5"
    @click="$emit('click')"
  >
    <AppIcon name="plus" />
    {{ label }}
  </BaseButton>
  <Teleport to="body">
    <BaseButton
      variant="primary"
      shape="circle"
      :title="label"
      class="fixed bottom-18 right-6 z-10 size-14 lg:hidden"
      @click="$emit('click')"
    >
      <AppIcon name="plus" :alt="label" />
    </BaseButton>
  </Teleport>
</template>

<script>
import AppIcon from '@/components/common/AppIcon.vue'
import BaseButton from '@/components/common/BaseButton.vue'

export default {
  name: 'AddButton',
  components: { AppIcon, BaseButton },
  props: {
    label: { type: String, required: true },
  },
  emits: ['click'],
}
</script>

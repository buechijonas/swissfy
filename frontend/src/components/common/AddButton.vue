<template>
  <BaseButton
    variant="primary"
    size="sm"
    class="hidden lg:inline-flex -my-1.5"
    :aria-busy="loading"
    @click="!loading && $emit('click')"
  >
    <span v-if="loading" class="loading loading-spinner loading-xs"></span>
    <AppIcon v-else :name="icon" />
    {{ label }}
  </BaseButton>
</template>

<script>
import AppIcon from '@/components/common/AppIcon.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import { useAddButtonStore } from '@/stores/addButton.js'

export default {
  name: 'AddButton',
  components: { AppIcon, BaseButton },
  props: {
    label: { type: String, required: true },
    icon: { type: String, default: 'plus' },
    loading: { type: Boolean, default: false },
  },
  emits: ['click'],
  computed: {
    config() {
      return {
        label: this.label,
        icon: this.icon,
        loading: this.loading,
        onClick: () => this.$emit('click'),
      }
    },
  },
  watch: {
    config: {
      immediate: true,
      handler(config) {
        useAddButtonStore().show(this.owner, config)
      },
    },
  },
  beforeCreate() {
    this.owner = Symbol('AddButton')
  },
  beforeUnmount() {
    useAddButtonStore().hide(this.owner)
  },
}
</script>

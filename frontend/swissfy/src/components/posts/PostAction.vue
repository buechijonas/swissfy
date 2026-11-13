<template>
  <div class="flex flex-col gap-1" :class="align === 'end' ? 'items-end' : 'items-center'">
    <component
      :is="interactive ? 'button' : 'span'"
      :type="interactive ? 'button' : null"
      class="relative flex size-6 box-content p-2.5 -m-2.5"
      :class="{ 'cursor-pointer': interactive }"
      :disabled="interactive && disabled"
      :title="title"
      @click.stop="select"
    >
      <AppIcon :name="icon" :alt="title" class="size-6!" :class="iconClass" />
    </component>
    <span v-if="label !== null" class="text-xs leading-4" :class="labelClass">{{ label }}</span>
  </div>
</template>

<script>
import AppIcon from '@core/components/AppIcon.vue'

export default {
  name: 'PostAction',
  components: { AppIcon },
  props: {
    icon: { type: String, required: true },
    title: { type: String, required: true },
    label: { type: [String, Number], default: null },
    interactive: { type: Boolean, default: true },
    disabled: { type: Boolean, default: false },
    align: { type: String, default: 'center' },
    iconClass: { type: [String, Array, Object], default: '' },
    labelClass: { type: [String, Array, Object], default: '' },
  },
  emits: ['select'],
  methods: {
    select() {
      if (this.interactive) this.$emit('select')
    },
  },
}
</script>

<template>
  <dialog ref="dialog" class="modal">
    <div class="modal-box flex flex-col" :class="boxClass">
      <form method="dialog">
        <BaseButton
          type="submit"
          variant="ghost"
          shape="circle"
          size="sm"
          class="absolute right-2 top-2"
          title="Schliessen"
        >
          <AppIcon name="cross" size="sm" alt="Schliessen" />
        </BaseButton>
      </form>
      <slot name="header">
        <h3 v-if="title" class="text-lg font-bold">{{ title }}</h3>
      </slot>
      <div class="py-4 flex-1 min-h-0 flex flex-col">
        <slot>
          <p v-if="description">{{ description }}</p>
        </slot>
      </div>
      <div v-if="buttons.length || $slots.actions" class="modal-action">
        <slot name="actions">
          <BaseButton
            v-for="button in buttons"
            :key="button.value"
            :variant="button.variant ?? 'neutral'"
            :outline="button.outline"
            @click="handleClick(button)"
          >
            <AppIcon v-if="button.icon" :name="button.icon" />
            {{ button.label }}
          </BaseButton>
        </slot>
      </div>
    </div>
    <form method="dialog" class="modal-backdrop">
      <button>close</button>
    </form>
  </dialog>
</template>

<script>
import AppIcon from '@/components/common/AppIcon.vue'
import BaseButton from '@/components/common/BaseButton.vue'

export default {
  name: 'BaseDialog',
  components: { AppIcon, BaseButton },
  props: {
    title: { type: String, default: '' },
    description: { type: String, default: '' },
    buttons: { type: Array, default: () => [] },
    boxClass: { type: [String, Array, Object], default: '' },
  },
  emits: ['action'],
  methods: {
    open() {
      this.$refs.dialog?.showModal()
    },
    close() {
      this.$refs.dialog?.close()
    },
    handleClick(button) {
      this.$refs.dialog?.close()
      this.$emit('action', button.value)
    },
  },
}
</script>

<template>
  <BaseDialog
    ref="dialog"
    :title="title"
    :description="message"
    :buttons="buttons"
    @action="onAction"
  />
</template>

<script>
import BaseDialog from '@/components/common/BaseDialog.vue'

export default {
  name: 'ConfirmDialog',
  components: { BaseDialog },
  props: {
    title: { type: String, default: 'Löschen bestätigen' },
    message: { type: String, required: true },
    confirmLabel: { type: String, default: 'Löschen' },
    cancelLabel: { type: String, default: 'Abbrechen' },
  },
  emits: ['confirm'],
  computed: {
    buttons() {
      return [
        { value: 'cancel', label: this.cancelLabel, icon: 'cross' },
        {
          value: 'confirm',
          label: this.confirmLabel,
          variant: 'error',
          outline: true,
          icon: 'trash',
        },
      ]
    },
  },
  methods: {
    open() {
      this.$refs.dialog?.open()
    },
    onAction(value) {
      if (value === 'confirm') this.$emit('confirm')
    },
  },
}
</script>

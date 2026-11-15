<template>
  <BaseDialog
    ref="dialog"
    :title="titleText"
    :description="message"
    :buttons="buttons"
    @action="onAction"
  />
</template>

<script>
import BaseDialog from '@/components/common/BaseDialog.vue'
import { t } from '@/i18n.js'

export default {
  name: 'ConfirmDialog',
  components: { BaseDialog },
  props: {
    title: { type: String, default: null },
    message: { type: String, required: true },
    confirmLabel: { type: String, default: null },
    confirmIcon: { type: String, default: 'trash' },
    confirmVariant: { type: String, default: 'error' },
    cancelLabel: { type: String, default: null },
  },
  emits: ['confirm'],
  computed: {
    titleText() {
      return this.title ?? t('dialog.confirmDelete')
    },
    buttons() {
      return [
        { value: 'cancel', label: this.cancelLabel ?? t('common.cancel'), icon: 'cross' },
        {
          value: 'confirm',
          label: this.confirmLabel ?? t('common.delete'),
          variant: this.confirmVariant,
          outline: true,
          icon: this.confirmIcon,
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

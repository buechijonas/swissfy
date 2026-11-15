<template>
  <AppIcon
    :name="status === 'sent' ? 'check' : 'check-double'"
    :alt="labels[status]"
    size="sm"
    :class="{ 'text-primary': status === 'read' }"
  />
</template>

<script>
import AppIcon from '@core/components/AppIcon.vue'
import { t } from '@/i18n.js'

export default {
  name: 'MessageStatus',
  components: { AppIcon },
  props: {
    status: { type: String, required: true },
  },
  computed: {
    labels() {
      return {
        sent: t('messageStatus.sent'),
        delivered: t('messageStatus.delivered'),
        read: t('messageStatus.read'),
      }
    },
  },
}
</script>

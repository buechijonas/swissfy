<template>
  <AppIcon
    :name="status === 'sent' ? 'check' : 'check-double'"
    :alt="labels[status]"
    size="sm"
    :class="{ 'text-primary': status === 'read' }"
  />
</template>

<script>
import AppIcon from '@/components/common/AppIcon.vue'

export default {
  name: 'MessageStatus',
  components: { AppIcon },
  props: {
    status: { type: String, required: true },
  },
  data() {
    return { labels: { sent: 'Gesendet', delivered: 'Angekommen', read: 'Gelesen' } }
  },
}
</script>

<template>
  <img
    v-if="role && badges[role.key]"
    class="size-4 shrink-0"
    :src="badges[role.key]"
    :alt="role.label"
    :title="role.label"
  />
</template>

<script>
import { badges } from '@/assets/images.js'

export default {
  name: 'RoleBadge',
  props: {
    role: { type: Object, default: null },
  },
  data() {
    return { badges }
  },
}
</script>

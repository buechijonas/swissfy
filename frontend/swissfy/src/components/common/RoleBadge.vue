<template>
  <img
    v-if="role && badges[role.key]"
    class="size-4 shrink-0"
    :src="badges[role.key]"
    :alt="$t(`roles.${role.key}`)"
    :title="$t(`roles.${role.key}`)"
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

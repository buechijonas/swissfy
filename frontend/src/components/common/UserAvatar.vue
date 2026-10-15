<template>
  <img
    class="shrink-0"
    :class="{ 'rounded-full object-cover': user?.picture }"
    :src="avatarSrc(user) ?? icons.user"
    :alt="alt"
  />
</template>

<script>
import { icons } from '@/assets/icons.js'
import { avatarSrc } from '@/lib/avatar.js'

export default {
  name: 'UserAvatar',
  props: {
    user: { type: Object, default: null },
    alt: { type: String, default: '' },
  },
  data() {
    return { icons }
  },
  methods: { avatarSrc },
}
</script>

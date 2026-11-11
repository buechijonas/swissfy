<template>
  <img
    class="shrink-0"
    :class="{
      'rounded-full object-cover': user?.picture,
      'rounded-full ring-2 ring-offset-2 ring-offset-base-100': storyRing,
      'ring-primary': storyRing && !storySeen,
      'ring-swissfy-muted': storyRing && storySeen,
    }"
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
    storyRing: { type: Boolean, default: false },
    storySeen: { type: Boolean, default: false },
  },
  data() {
    return { icons }
  },
  methods: { avatarSrc },
}
</script>

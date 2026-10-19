<template>
  <RouterLink :to="link" class="relative">
    <img
      class="aspect-square w-full object-cover bg-base-200"
      :src="post.thumbnail"
      alt=""
      loading="lazy"
    />
    <AppIcon
      v-if="post.video"
      name="clapperboard-play"
      alt="Video"
      class="absolute top-2 right-2 size-5! text-white drop-shadow"
    />
  </RouterLink>
</template>

<script>
import { RouterLink } from 'vue-router'
import AppIcon from '@/components/common/AppIcon.vue'

export default {
  name: 'PostTile',
  components: { RouterLink, AppIcon },
  props: {
    post: { type: Object, required: true },
    reelBase: { type: String, default: null },
  },
  computed: {
    link() {
      if (!this.post.video) return `/posts/${this.post.id}`
      const base =
        this.reelBase ?? `/profile/${encodeURIComponent(this.post.author.username)}/reels`
      return `${base}/${this.post.id}`
    },
  },
}
</script>

<template>
  <header
    class="flex cursor-pointer items-center gap-3 px-4 py-3 border-b border-swissfy-border"
    @click="openProfile"
  >
    <RouterLink :to="profileLink" class="flex items-center gap-3 min-w-0">
      <img class="size-10 shrink-0" :src="avatarSrc" alt="" />
      <div class="flex flex-col min-w-0">
        <span class="font-bold truncate">{{ fullName || author.username }}</span>
        <span class="text-swissfy-muted text-sm truncate">@{{ author.username }}</span>
      </div>
    </RouterLink>
    <div class="ml-auto flex shrink-0 items-center gap-2">
      <slot />
    </div>
  </header>
</template>

<script>
import { RouterLink } from 'vue-router'
import { icons } from '@/assets/icons.js'
import { avatars } from '@/assets/images.js'

export default {
  name: 'AuthorHeader',
  components: { RouterLink },
  props: {
    author: { type: Object, required: true },
  },
  methods: {
    openProfile(event) {
      if (event.target.closest('a, button, dialog')) return
      this.$router.push(this.profileLink)
    },
  },
  computed: {
    profileLink() {
      return `/profile/${encodeURIComponent(this.author.username)}`
    },
    avatarSrc() {
      return avatars[this.author.avatar] ?? icons.user
    },
    fullName() {
      return [this.author.first_name, this.author.last_name].filter(Boolean).join(' ')
    },
  },
}
</script>

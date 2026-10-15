<template>
  <header
    class="flex cursor-pointer items-center gap-3 px-4 py-3"
    :class="
      overlay
        ? 'bg-linear-to-b from-black/60 to-transparent pb-8 text-white [text-shadow:0_1px_2px_rgb(0_0_0/0.6)] [&_.btn-outline:not(.btn-error)]:border-white/70 [&_.btn-outline:not(.btn-error)]:text-white'
        : 'border-b border-swissfy-border'
    "
    @click="openProfile"
  >
    <RouterLink :to="profileLink" class="flex items-center gap-3 min-w-0">
      <UserAvatar class="size-10" :user="author" />
      <div class="flex flex-col min-w-0">
        <span class="flex min-w-0 items-center gap-2">
          <span class="font-bold truncate">{{ fullName || author.username }}</span>
          <RoleBadge :role="author.role" />
        </span>
        <span class="text-sm truncate" :class="overlay ? 'text-white/80' : 'text-swissfy-muted'"
          >@{{ author.username }}</span
        >
      </div>
    </RouterLink>
    <div class="ml-auto flex shrink-0 items-center gap-2">
      <slot />
    </div>
  </header>
</template>

<script>
import { RouterLink } from 'vue-router'
import RoleBadge from '@/components/common/RoleBadge.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'

export default {
  name: 'AuthorHeader',
  components: { RouterLink, RoleBadge, UserAvatar },
  props: {
    author: { type: Object, required: true },
    overlay: { type: Boolean, default: false },
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
    fullName() {
      return [this.author.first_name, this.author.last_name].filter(Boolean).join(' ')
    },
  },
}
</script>

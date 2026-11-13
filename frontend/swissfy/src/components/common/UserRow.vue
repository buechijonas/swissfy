<template>
  <RouterLink :to="to" class="flex items-center gap-4 px-6 py-3 hover:bg-base-200">
    <UserAvatar class="size-12" :user="user" />
    <div class="flex flex-col min-w-0 flex-1">
      <span class="flex min-w-0 items-center gap-2">
        <CipherText v-if="!user.can_view" :length="10" class="font-bold" />
        <span v-else class="font-bold truncate">{{ user.display_name }}</span>
        <RoleBadge :role="user.role" />
      </span>
      <slot name="subtitle">
        <span class="text-app-muted text-sm truncate">@{{ user.username }}</span>
      </slot>
    </div>
    <div v-if="$slots.default" class="flex flex-col items-end gap-1 min-w-0 max-w-[45%] text-right">
      <slot />
    </div>
  </RouterLink>
</template>

<script>
import { RouterLink } from 'vue-router'
import CipherText from '@/components/common/CipherText.vue'
import RoleBadge from '@/components/common/RoleBadge.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'

export default {
  name: 'UserRow',
  components: { RouterLink, CipherText, RoleBadge, UserAvatar },
  props: {
    user: { type: Object, required: true },
    to: { type: [String, Object], required: true },
  },
  computed: {},
}
</script>

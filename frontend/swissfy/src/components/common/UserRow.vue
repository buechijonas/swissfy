<template>
  <RouterLink :to="to" class="flex items-center gap-4 px-6 py-3 hover:bg-base-200">
    <UserAvatar class="size-12" :user="user" />
    <div class="flex min-w-0 flex-1 flex-col">
      <span class="flex min-w-0 items-center gap-2">
        <CipherText v-if="!user.can_view" :length="10" class="font-bold" />
        <span v-else class="truncate font-bold">{{ user.display_name }}</span>
        <RoleBadge :role="user.role" />
      </span>
      <slot name="subtitle">
        <span class="truncate text-sm text-app-muted">@{{ user.username }}</span>
      </slot>
    </div>
    <div v-if="$slots.default" class="flex max-w-[45%] min-w-0 flex-col items-end gap-1 text-right">
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

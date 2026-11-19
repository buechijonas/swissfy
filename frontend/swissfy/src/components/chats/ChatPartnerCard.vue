<template>
  <BaseCard v-if="partner" class="flex items-center gap-4 px-4 py-3 max-sm:border-t-0 sm:mt-4">
    <RouterLink :to="profileLink" class="flex min-w-0 items-center gap-4">
      <UserAvatar class="size-12" :user="partner" />
      <div class="flex min-w-0 flex-col">
        <span class="flex min-w-0 items-center gap-2">
          <CipherText v-if="!partner.can_view" :length="10" class="font-bold" />
          <span v-else class="truncate font-bold">{{ partner.display_name }}</span>
          <RoleBadge :role="partner.role" />
        </span>
        <span class="truncate text-sm text-app-muted">@{{ partner.username }}</span>
      </div>
    </RouterLink>
    <BaseButton
      v-if="encryption && verifiable"
      size="xs"
      variant="ghost"
      class="ml-auto shrink-0 text-app-muted"
      :aria-label="$t('chat.safetyNumber')"
      @click="$emit('verify')"
    >
      <AppIcon name="shield-trust" size="sm" />
      {{ encryption }}
    </BaseButton>
    <span
      v-else-if="encryption"
      class="ml-auto flex shrink-0 items-center gap-2 text-xs text-app-muted"
    >
      <AppIcon name="lock" size="sm" />
      {{ encryption }}
    </span>
  </BaseCard>
  <BaseCard v-else class="flex items-center gap-4 px-4 py-3 max-sm:border-t-0 sm:mt-4">
    <div class="size-12 skeleton rounded-full"></div>
    <div class="flex flex-col gap-2">
      <div class="h-4 w-40 skeleton"></div>
      <div class="h-3 w-24 skeleton"></div>
    </div>
  </BaseCard>
</template>

<script>
import { RouterLink } from 'vue-router'
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import BaseCard from '@core/components/BaseCard.vue'
import CipherText from '@/components/common/CipherText.vue'
import RoleBadge from '@/components/common/RoleBadge.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'

export default {
  name: 'ChatPartnerCard',
  components: { RouterLink, AppIcon, BaseButton, BaseCard, CipherText, RoleBadge, UserAvatar },
  props: {
    partner: { type: Object, default: null },
    encryption: { type: String, default: null },
    verifiable: { type: Boolean, default: false },
  },
  emits: ['verify'],
  computed: {
    profileLink() {
      return `/profile/${encodeURIComponent(this.partner.username)}`
    },
  },
}
</script>

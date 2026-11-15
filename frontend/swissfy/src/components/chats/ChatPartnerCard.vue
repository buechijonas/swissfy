<template>
  <BaseCard v-if="partner" class="sm:mt-4 max-sm:border-t-0 px-4 py-3 flex items-center gap-4">
    <RouterLink :to="profileLink" class="flex items-center gap-4 min-w-0">
      <UserAvatar class="size-12" :user="partner" />
      <div class="flex flex-col min-w-0">
        <span class="flex min-w-0 items-center gap-2">
          <CipherText v-if="!partner.can_view" :length="10" class="font-bold" />
          <span v-else class="font-bold truncate">{{ partner.display_name }}</span>
          <RoleBadge :role="partner.role" />
        </span>
        <span class="text-app-muted text-sm truncate">@{{ partner.username }}</span>
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
      class="ml-auto flex items-center gap-2 text-xs text-app-muted shrink-0"
    >
      <AppIcon name="lock" size="sm" />
      {{ encryption }}
    </span>
  </BaseCard>
  <BaseCard v-else class="sm:mt-4 max-sm:border-t-0 px-4 py-3 flex items-center gap-4">
    <div class="skeleton size-12 rounded-full"></div>
    <div class="flex flex-col gap-2">
      <div class="skeleton h-4 w-40"></div>
      <div class="skeleton h-3 w-24"></div>
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

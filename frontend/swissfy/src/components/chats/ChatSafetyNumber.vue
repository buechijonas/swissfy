<template>
  <BaseCard class="p-4 flex flex-col gap-3 border-t-0">
    <p v-if="changed" class="flex items-start gap-2 text-warning text-sm">
      <AppIcon name="shield-exclamation" size="sm" class="mt-0.5 shrink-0" />
      {{ $t('chat.keysChanged', { username }) }}
    </p>
    <p class="text-app-muted text-sm">{{ $t('chat.safetyNumberHint') }}</p>
    <p class="font-mono text-lg tracking-widest text-center">{{ groups.join(' ') }}</p>
    <div v-if="changed" class="flex justify-end">
      <BaseButton size="sm" variant="primary" @click="$emit('accept')">
        <AppIcon name="check" />
        {{ $t('chat.keysAccepted') }}
      </BaseButton>
    </div>
  </BaseCard>
</template>

<script>
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import BaseCard from '@core/components/BaseCard.vue'

export default {
  name: 'ChatSafetyNumber',
  components: { AppIcon, BaseButton, BaseCard },
  props: {
    username: { type: String, required: true },
    groups: { type: Array, required: true },
    changed: { type: Boolean, default: false },
  },
  emits: ['accept'],
}
</script>

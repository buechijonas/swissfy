<template>
  <BaseCard class="flex flex-col gap-3 border-t-0 p-4">
    <p v-if="changed" class="flex items-start gap-2 text-sm text-warning">
      <AppIcon name="shield-exclamation" size="sm" class="mt-0.5 shrink-0" />
      {{ $t('chat.keysChanged', { username }) }}
    </p>
    <p class="text-sm text-app-muted">{{ $t('chat.safetyNumberHint') }}</p>
    <p class="text-center font-mono text-lg tracking-widest">{{ groups.join(' ') }}</p>
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

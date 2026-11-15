<template>
  <form class="flex items-end gap-2 my-4" @submit.prevent="submit">
    <textarea
      :value="modelValue"
      rows="1"
      :maxlength="maxLength"
      class="textarea flex-1 min-h-10 resize-none"
      :placeholder="blockedReason || $t('chat.message')"
      :disabled="Boolean(blockedReason)"
      @input="$emit('update:modelValue', $event.target.value)"
      @keydown.enter.exact.prevent="submit"
    ></textarea>
    <BaseButton type="submit" variant="primary" class="min-w-12" :disabled="!canSend">
      <template v-if="cooldown">{{ cooldown }} s</template>
      <AppIcon v-else name="paper-plane-top" :alt="$t('chat.send')" />
    </BaseButton>
  </form>
</template>

<script>
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'

const MAX_LENGTH = 2000

export default {
  name: 'ChatComposer',
  components: { AppIcon, BaseButton },
  props: {
    modelValue: { type: String, required: true },
    blockedReason: { type: String, default: null },
    cooldown: { type: Number, required: true },
    sending: { type: Boolean, required: true },
  },
  emits: ['update:modelValue', 'submit'],
  data() {
    return { maxLength: MAX_LENGTH }
  },
  computed: {
    canSend() {
      return !this.sending && !this.cooldown && !this.blockedReason && this.modelValue.trim() !== ''
    },
  },
  methods: {
    submit() {
      if (this.canSend) this.$emit('submit')
    },
  },
}
</script>

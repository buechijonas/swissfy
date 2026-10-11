<template>
  <form class="flex gap-2" @submit.prevent="$emit('submit')">
    <input
      :value="modelValue"
      class="input flex-1"
      :maxlength="maxLength"
      :placeholder="placeholder"
      @input="$emit('update:modelValue', $event.target.value)"
    />
    <BaseButton
      type="submit"
      variant="primary"
      shape="square"
      :disabled="sending || !modelValue.trim()"
      title="Senden"
    >
      <AppIcon name="paper-plane-top" alt="Senden" />
    </BaseButton>
  </form>
</template>

<script>
import AppIcon from '@/components/common/AppIcon.vue'
import BaseButton from '@/components/common/BaseButton.vue'

const MAX_LENGTH = 500

export default {
  name: 'CommentForm',
  components: { AppIcon, BaseButton },
  props: {
    modelValue: { type: String, required: true },
    placeholder: { type: String, required: true },
    sending: { type: Boolean, default: false },
  },
  emits: ['update:modelValue', 'submit'],
  data() {
    return { maxLength: MAX_LENGTH }
  },
}
</script>

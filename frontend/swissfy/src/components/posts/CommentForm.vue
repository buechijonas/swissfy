<template>
  <form class="flex gap-2" @submit.prevent="$emit('submit')">
    <input v-model="text" class="input flex-1" :maxlength="maxLength" :placeholder="placeholder" />
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
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'

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
  computed: {
    text: {
      get() {
        return this.modelValue
      },
      set(text) {
        this.$emit('update:modelValue', text)
      },
    },
  },
}
</script>

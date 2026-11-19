<template>
  <select
    v-model="selected"
    class="select w-auto select-sm"
    :disabled="disabled"
    :title="titleText"
  >
    <option v-for="option in roles" :key="option.value" :value="option.value">
      {{ $t(`roles.${option.value}`) }}
    </option>
  </select>
</template>

<script>
import { t } from '@/i18n.js'

export default {
  name: 'RoleSelect',
  props: {
    role: { type: String, required: true },
    roles: { type: Array, required: true },
    disabled: { type: Boolean, default: false },
    title: { type: String, default: null },
  },
  emits: ['change'],
  computed: {
    titleText() {
      return this.title ?? t('administration.role')
    },
    selected: {
      get() {
        return this.role
      },
      set(role) {
        this.$emit('change', role)
      },
    },
  },
}
</script>

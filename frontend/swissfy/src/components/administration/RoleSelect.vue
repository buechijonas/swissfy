<template>
  <select
    v-model="selected"
    class="select select-sm w-auto"
    :disabled="disabled"
    :title="titleText"
  >
    <option v-for="role in roles" :key="role.value" :value="role.value">
      {{ $t(`roles.${role.value}`) }}
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

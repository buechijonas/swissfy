<template>
  <select v-model="selected" class="select select-sm w-auto" :disabled="disabled" :title="title">
    <option v-for="role in roles" :key="role.value" :value="role.value">
      {{ role.label }}
    </option>
  </select>
</template>

<script>
export default {
  name: 'RoleSelect',
  props: {
    role: { type: String, required: true },
    roles: { type: Array, required: true },
    disabled: { type: Boolean, default: false },
    title: { type: String, default: 'Rolle' },
  },
  emits: ['change'],
  computed: {
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

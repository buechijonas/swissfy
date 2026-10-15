<template>
  <p class="mb-2 text-sm">Sichtbar für</p>
  <div class="flex flex-wrap gap-2">
    <BaseButton
      v-for="option in shownOptions"
      :key="option.value"
      size="sm"
      :variant="visibility === option.value ? 'primary' : 'neutral'"
      @click="$emit('update:visibility', option.value)"
    >
      <AppIcon :name="option.icon" />
      {{ option.label }}
    </BaseButton>
  </div>
  <div v-if="visibility === 'groups'" class="mt-3 flex flex-col gap-2">
    <label v-for="group in groupList" :key="group.id" class="flex items-center gap-2">
      <input
        :checked="groups.includes(group.id)"
        type="checkbox"
        class="checkbox checkbox-sm"
        @change="toggleGroup(group.id, $event.target.checked)"
      />
      {{ group.name }}
    </label>
    <p v-if="!groupList.length" class="text-sm text-swissfy-muted">
      Du hast noch keine Gruppen.
      <RouterLink to="/settings?tab=groups" class="link">Gruppen anlegen</RouterLink>
    </p>
  </div>
</template>

<script>
import { RouterLink } from 'vue-router'
import AppIcon from '@/components/common/AppIcon.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import { useGroupsStore } from '@/stores/posts.js'

export default {
  name: 'VisibilityPicker',
  components: { RouterLink, AppIcon, BaseButton },
  props: {
    visibility: { type: String, required: true },
    groups: { type: Array, required: true },
    allowPublic: { type: Boolean, default: true },
  },
  emits: ['update:visibility', 'update:groups'],
  data() {
    return {
      options: [
        { value: 'public', label: 'Alle', icon: 'globe' },
        { value: 'followers', label: 'Follower', icon: 'user' },
        { value: 'friends', label: 'Freunde', icon: 'users' },
        { value: 'groups', label: 'Gruppen', icon: 'users-alt' },
      ],
    }
  },
  computed: {
    shownOptions() {
      return this.options.filter((option) => this.allowPublic || option.value !== 'public')
    },
    groupList() {
      return useGroupsStore().items ?? []
    },
  },
  methods: {
    toggleGroup(id, checked) {
      const groups = this.groups.filter((group) => group !== id)
      this.$emit('update:groups', checked ? [...groups, id] : groups)
    },
  },
}
</script>

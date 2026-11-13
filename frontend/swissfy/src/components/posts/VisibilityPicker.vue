<template>
  <p class="mb-2 text-sm">Sichtbar für</p>
  <div class="grid gap-2" :class="gridClass">
    <BaseButton
      v-for="option in shownOptions"
      :key="option.value"
      :class="{ 'col-span-full': option.adminOnly }"
      :variant="visibility === option.value ? 'primary' : 'neutral'"
      @click="$emit('update:visibility', option.value)"
    >
      <AppIcon :name="option.icon" />
      {{ option.label }}
    </BaseButton>
  </div>
  <p v-if="visibility === 'global'" class="mt-3 text-sm text-app-muted">
    Erscheint bei allen im Feed auf der Startseite, auch bei Leuten, die dir nicht folgen.
  </p>
  <div v-if="visibility === 'groups'" class="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3">
    <label
      v-for="group in groupList"
      :key="group.id"
      class="flex min-w-0 items-center gap-3 text-sm"
    >
      <input
        v-model="selectedGroups"
        :value="group.id"
        type="checkbox"
        class="size-8 shrink-0 accent-primary"
      />
      <span class="truncate">{{ group.name }}</span>
    </label>
    <p v-if="!groupList.length" class="col-span-full text-sm text-app-muted">
      Du hast noch keine Gruppen.
      <RouterLink to="/settings?tab=groups" class="link">Gruppen anlegen</RouterLink>
    </p>
  </div>
</template>

<script>
import { mapStores } from 'pinia'
import { RouterLink } from 'vue-router'
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import { useAuthStore } from '@/stores/auth.js'
import { useGroupsStore } from '@/stores/posts.js'

export default {
  name: 'VisibilityPicker',
  components: { RouterLink, AppIcon, BaseButton },
  props: {
    visibility: { type: String, required: true },
    groups: { type: Array, required: true },
    allowPublic: { type: Boolean, default: true },
    allowGlobal: { type: Boolean, default: true },
  },
  emits: ['update:visibility', 'update:groups'],
  data() {
    return {
      options: [
        { value: 'public', label: 'Alle', icon: 'users-alt' },
        { value: 'followers', label: 'Follower', icon: 'fire-flame-curved' },
        { value: 'friends', label: 'Freunde', icon: 'high-five-celebration-yes' },
        { value: 'groups', label: 'Gruppen', icon: 'resources' },
        { value: 'global', label: 'Global', icon: 'world', adminOnly: true },
      ],
    }
  },
  computed: {
    ...mapStores(useAuthStore),
    selectedGroups: {
      get() {
        return this.groups
      },
      set(groups) {
        this.$emit('update:groups', groups)
      },
    },
    canPostGlobally() {
      return Boolean(this.authStore.user?.permissions.post_globally)
    },
    gridClass() {
      const columns = this.shownOptions.filter((option) => !option.adminOnly).length
      return columns === 4 ? 'grid-cols-2 sm:grid-cols-4' : 'grid-cols-3'
    },
    shownOptions() {
      return this.options.filter((option) => {
        if (option.adminOnly) return this.allowPublic && this.allowGlobal && this.canPostGlobally
        return this.allowPublic || option.value !== 'public'
      })
    },
    groupList() {
      return useGroupsStore().items ?? []
    },
  },
}
</script>

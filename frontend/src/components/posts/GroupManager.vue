<template>
  <BaseCard class="p-6">
    <p class="text-swissfy-muted text-sm mb-4">
      Mit Gruppen bestimmst du, wer einen Post sieht. Nur du siehst deine Gruppen.
    </p>
    <form class="flex gap-2" @submit.prevent="createGroup">
      <input v-model="newName" class="input flex-1" maxlength="50" placeholder="Neue Gruppe" />
      <BaseButton type="submit" variant="primary" :disabled="!newName.trim()">
        <AppIcon name="plus" />
        Anlegen
      </BaseButton>
    </form>
  </BaseCard>

  <p v-if="error" class="text-error text-sm mt-4 text-center">{{ error }}</p>

  <BaseCard v-for="group in groups" :key="group.id" class="p-6 mt-4 flex flex-col gap-3">
    <div class="flex items-center gap-2">
      <AppIcon name="users" />
      <h4 class="font-bold truncate">{{ group.name }}</h4>
      <DeleteButton class="ml-auto" @click="confirmDelete(group)" />
    </div>
    <div class="flex flex-wrap gap-2">
      <span v-for="member in group.members" :key="member" class="badge badge-neutral gap-1">
        @{{ member }}
        <button
          type="button"
          :aria-label="`${member} entfernen`"
          @click="removeMember(group, member)"
        >
          <AppIcon name="cross" size="sm" />
        </button>
      </span>
      <span v-if="!group.members.length" class="text-sm text-swissfy-muted">Noch niemand.</span>
    </div>
    <form class="flex gap-2" @submit.prevent="addMember(group)">
      <input v-model="drafts[group.id]" class="input input-sm flex-1" placeholder="Benutzername" />
      <BaseButton type="submit" size="sm" :disabled="!drafts[group.id]?.trim()">
        Hinzufügen
      </BaseButton>
    </form>
  </BaseCard>

  <ConfirmDialog
    ref="confirm"
    :message="`Gruppe «${pendingDelete?.name}» löschen?`"
    @confirm="deleteGroup"
  />
</template>

<script>
import AppIcon from '@/components/common/AppIcon.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import DeleteButton from '@/components/common/DeleteButton.vue'
import { useGroupsStore } from '@/stores/posts.js'

export default {
  name: 'GroupManager',
  components: { AppIcon, BaseButton, BaseCard, ConfirmDialog, DeleteButton },
  data() {
    return {
      newName: '',
      drafts: {},
      pendingDelete: null,
      error: null,
    }
  },
  computed: {
    groupsStore() {
      return useGroupsStore()
    },
    groups() {
      return this.groupsStore.items ?? []
    },
  },
  created() {
    this.run(() => this.groupsStore.load())
  },
  methods: {
    async run(action) {
      this.error = null
      try {
        await action()
        return true
      } catch (error) {
        this.error = error.message
        return false
      }
    },
    async createGroup() {
      if (await this.run(() => this.groupsStore.create({ name: this.newName, members: [] }))) {
        this.newName = ''
      }
    },
    setMembers(group, members) {
      return this.run(() => this.groupsStore.update(group.id, { members }))
    },
    async addMember(group) {
      const username = this.drafts[group.id].trim().replace(/^@/, '')
      if (group.members.includes(username)) return
      if (await this.setMembers(group, [...group.members, username])) {
        this.drafts[group.id] = ''
      }
    },
    removeMember(group, member) {
      return this.setMembers(
        group,
        group.members.filter((name) => name !== member),
      )
    },
    confirmDelete(group) {
      this.pendingDelete = group
      this.$refs.confirm.open()
    },
    deleteGroup() {
      return this.run(() => this.groupsStore.remove(this.pendingDelete.id))
    },
  },
}
</script>

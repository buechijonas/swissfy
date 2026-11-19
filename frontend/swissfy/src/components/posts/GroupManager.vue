<template>
  <BaseCard class="p-6">
    <p class="mb-4 text-sm text-app-muted">
      {{ $t('groups.intro') }}
    </p>
    <form class="flex gap-2" @submit.prevent="createGroup">
      <input
        v-model="newName"
        class="input flex-1"
        maxlength="50"
        :placeholder="$t('groups.new')"
      />
      <BaseButton type="submit" variant="primary" :disabled="!newName.trim()">
        <AppIcon name="plus" />
        {{ $t('common.create') }}
      </BaseButton>
    </form>
  </BaseCard>

  <ErrorText :message="action.error" class="mt-4 text-center" />

  <BaseCard v-for="group in groups" :key="group.id" class="mt-4 flex flex-col gap-3 p-6">
    <div class="flex items-center gap-2">
      <AppIcon name="users" />
      <h4 class="truncate font-bold">{{ group.name }}</h4>
      <DeleteButton class="ml-auto" @click="confirmDelete(group)" />
    </div>
    <div class="flex flex-wrap gap-2">
      <span v-for="member in group.members" :key="member" class="badge gap-1 badge-neutral">
        @{{ member }}
        <button
          type="button"
          :aria-label="`${member} entfernen`"
          @click="removeMember(group, member)"
        >
          <AppIcon name="cross" size="sm" />
        </button>
      </span>
      <span v-if="!group.members.length" class="text-sm text-app-muted">{{
        $t('groups.empty')
      }}</span>
    </div>
    <form class="flex gap-2" @submit.prevent="addMember(group)">
      <input
        v-model="drafts[group.id]"
        class="input flex-1 input-sm"
        :placeholder="$t('groups.username')"
      />
      <BaseButton type="submit" size="sm" :disabled="!drafts[group.id]?.trim()">
        <AppIcon name="plus" />
        {{ $t('groups.add') }}
      </BaseButton>
    </form>
  </BaseCard>

  <ConfirmDialog
    ref="confirm"
    :message="$t('groups.deleteMessage', { name: pendingDelete?.name })"
    @confirm="deleteGroup"
  />
</template>

<script>
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import BaseCard from '@core/components/BaseCard.vue'
import ErrorText from '@core/components/ErrorText.vue'
import { useAsyncAction } from '@core/composables/asyncAction.js'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import DeleteButton from '@/components/common/DeleteButton.vue'
import { useGroupsStore } from '@/stores/posts.js'

export default {
  name: 'GroupManager',
  components: { AppIcon, BaseButton, BaseCard, ConfirmDialog, DeleteButton, ErrorText },
  data() {
    return {
      action: useAsyncAction(),
      newName: '',
      drafts: {},
      pendingDelete: null,
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
      await this.action.run(action)
      return !this.action.error
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

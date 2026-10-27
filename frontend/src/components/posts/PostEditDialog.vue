<template>
  <BaseDialog ref="dialog" title="Feed bearbeiten" class="modal-bottom sm:modal-middle">
    <VisibilityPicker v-model:visibility="visibility" v-model:groups="groups" />
    <p v-if="error" class="text-error text-sm mt-4">{{ error }}</p>
    <BaseButton
      variant="error"
      outline
      block
      class="mt-6"
      :disabled="busy"
      @click="$refs.confirm.open()"
    >
      <AppIcon name="trash" />
      Feed löschen
    </BaseButton>
    <template #actions>
      <BaseButton @click="$refs.dialog.close()">
        <AppIcon name="cross" />
        Abbrechen
      </BaseButton>
      <BaseButton variant="primary" :disabled="!canSave" @click="save">
        <AppIcon name="disk" />
        Speichern
      </BaseButton>
    </template>
  </BaseDialog>
  <ConfirmDialog ref="confirm" message="Willst du diesen Feed löschen?" @confirm="remove" />
</template>

<script>
import AppIcon from '@/components/common/AppIcon.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import VisibilityPicker from '@/components/posts/VisibilityPicker.vue'
import postsApi from '@/api/posts.js'
import { useGroupsStore } from '@/stores/posts.js'

export default {
  name: 'PostEditDialog',
  components: { AppIcon, BaseButton, BaseDialog, ConfirmDialog, VisibilityPicker },
  props: {
    post: { type: Object, required: true },
  },
  emits: ['updated', 'deleted'],
  data() {
    return {
      visibility: 'public',
      groups: [],
      busy: false,
      error: null,
    }
  },
  computed: {
    canSave() {
      return !this.busy && (this.visibility !== 'groups' || this.groups.length > 0)
    },
  },
  methods: {
    open() {
      this.visibility = this.post.visibility
      this.groups = [...this.post.groups]
      this.error = null
      useGroupsStore()
        .load()
        .catch(() => {})
      this.$refs.dialog.open()
    },
    async run(action, fallback) {
      this.busy = true
      this.error = null
      try {
        await action()
      } catch (error) {
        this.error = error.detail ?? fallback
      } finally {
        this.busy = false
      }
    },
    save() {
      return this.run(async () => {
        const body = { visibility: this.visibility, groups: this.groups }
        const post = await postsApi.update(this.post.id, body)
        this.$refs.dialog.close()
        this.$emit('updated', post)
      }, 'Feed konnte nicht gespeichert werden.')
    },
    remove() {
      return this.run(async () => {
        await postsApi.remove(this.post.id)
        this.$refs.dialog.close()
        this.$emit('deleted', this.post.id)
      }, 'Feed konnte nicht gelöscht werden.')
    },
  },
}
</script>

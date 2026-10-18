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
import { apiFetch, extractErrorMessage } from '@/lib/api.js'
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
    url() {
      return `/api/posts/${this.post.id}/`
    },
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
    async request(method, body, fallback) {
      this.busy = true
      this.error = null
      try {
        const response = await apiFetch(this.url, { method, body: body && JSON.stringify(body) })
        if (response.ok) return response
        this.error = extractErrorMessage(await response.json().catch(() => null), fallback)
      } catch {
        this.error = fallback
      } finally {
        this.busy = false
      }
      return null
    },
    async save() {
      const body = { visibility: this.visibility, groups: this.groups }
      const response = await this.request('PATCH', body, 'Feed konnte nicht gespeichert werden.')
      if (!response) return
      this.$refs.dialog.close()
      this.$emit('updated', await response.json())
    },
    async remove() {
      if (!(await this.request('DELETE', null, 'Feed konnte nicht gelöscht werden.'))) return
      this.$refs.dialog.close()
      this.$emit('deleted', this.post.id)
    },
  },
}
</script>

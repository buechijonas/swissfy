<template>
  <BaseDialog ref="dialog" :title="$t('postEdit.title')" class="modal-bottom sm:modal-middle">
    <VisibilityPicker v-model:visibility="visibility" v-model:groups="groups" />
    <ErrorText :message="action.error" class="mt-4" />
    <BaseButton
      variant="error"
      outline
      block
      class="mt-6"
      :disabled="action.busy"
      @click="$refs.confirm.open()"
    >
      <AppIcon name="trash" />
      {{ $t('postEdit.delete') }}
    </BaseButton>
    <template #actions>
      <BaseButton @click="$refs.dialog.close()">
        <AppIcon name="cross" />
        {{ $t('common.cancel') }}
      </BaseButton>
      <BaseButton variant="primary" :disabled="!canSave" @click="save">
        <AppIcon name="disk" />
        {{ $t('common.save') }}
      </BaseButton>
    </template>
  </BaseDialog>
  <ConfirmDialog ref="confirm" :message="$t('postEdit.deleteMessage')" @confirm="remove" />
</template>

<script>
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import ErrorText from '@core/components/ErrorText.vue'
import { useAsyncAction } from '@core/composables/asyncAction.js'
import postsApi from '@/api/posts.js'
import BaseDialog from '@/components/common/BaseDialog.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import VisibilityPicker from '@/components/posts/VisibilityPicker.vue'
import { t } from '@/i18n.js'
import { useGroupsStore } from '@/stores/posts.js'

export default {
  name: 'PostEditDialog',
  components: { AppIcon, BaseButton, BaseDialog, ConfirmDialog, VisibilityPicker, ErrorText },
  props: {
    post: { type: Object, required: true },
  },
  emits: ['updated', 'deleted'],
  data() {
    return {
      action: useAsyncAction(),
      visibility: 'public',
      groups: [],
    }
  },
  computed: {
    canSave() {
      return !this.action.busy && (this.visibility !== 'groups' || this.groups.length > 0)
    },
  },
  methods: {
    open() {
      this.visibility = this.post.visibility
      this.groups = [...this.post.groups]
      this.action.error = null
      useGroupsStore()
        .load()
        .catch(() => {})
      this.$refs.dialog.open()
    },
    save() {
      return this.action.run(async () => {
        const body = { visibility: this.visibility, groups: this.groups }
        const post = await postsApi.updateAudience(this.post.id, body)
        this.$refs.dialog.close()
        this.$emit('updated', post)
      }, t('postEdit.saveFailed'))
    },
    remove() {
      return this.action.run(async () => {
        await postsApi.remove(this.post.id)
        this.$refs.dialog.close()
        this.$emit('deleted', this.post.id)
      }, t('postEdit.deleteFailed'))
    },
  },
}
</script>

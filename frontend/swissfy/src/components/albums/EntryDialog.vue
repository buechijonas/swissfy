<template>
  <BaseDialog ref="dialog" :title="$t('albumEntry.edit')">
    <div v-if="entry" class="flex flex-col gap-4">
      <img :src="entry.post.thumbnail" alt="" class="size-24 bg-base-200 object-cover" />
      <label class="flex flex-col gap-1">
        <span class="text-sm text-app-muted">{{ $t('albumEntry.date') }}</span>
        <input v-model="date" type="date" class="input w-full" />
      </label>
      <label class="flex flex-col gap-1">
        <span class="text-sm text-app-muted">{{ $t('albumEntry.title') }}</span>
        <input v-model="title" class="input w-full" maxlength="50" @keyup.enter="save" />
      </label>
      <ErrorText :message="action.error" />
    </div>
    <template #actions>
      <BaseButton
        :title="$t('albumEntry.remove')"
        variant="error"
        outline
        class="mr-auto"
        :disabled="action.busy"
        @click="remove"
      >
        <AppIcon name="trash" />
        <span class="max-sm:hidden">{{ $t('albumEntry.remove') }}</span>
      </BaseButton>
      <BaseButton :title="$t('common.cancel')" @click="$refs.dialog.close()">
        <AppIcon name="cross" />
        <span class="max-sm:hidden">{{ $t('common.cancel') }}</span>
      </BaseButton>
      <BaseButton
        :title="$t('common.save')"
        variant="primary"
        :disabled="action.busy"
        @click="save"
      >
        <AppIcon name="disk" />
        <span class="max-sm:hidden">{{ $t('common.save') }}</span>
      </BaseButton>
    </template>
  </BaseDialog>
</template>

<script>
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import ErrorText from '@core/components/ErrorText.vue'
import { useAsyncAction } from '@core/composables/asyncAction.js'
import albumsApi from '@/api/albums.js'
import BaseDialog from '@/components/common/BaseDialog.vue'
import { t } from '@/i18n.js'

export default {
  name: 'EntryDialog',
  components: { AppIcon, BaseButton, BaseDialog, ErrorText },
  emits: ['saved'],
  data() {
    return {
      action: useAsyncAction(),
      entry: null,
      date: '',
      title: '',
    }
  },
  methods: {
    open(entry) {
      this.entry = entry
      this.date = entry.date ?? ''
      this.title = entry.title
      this.action.error = null
      this.$refs.dialog.open()
    },
    async request(action) {
      const album = await this.action.run(action, t('albumEntry.saveFailed'))
      if (!album) return
      this.$refs.dialog.close()
      this.$emit('saved', album)
    },
    save() {
      const body = { date: this.date || null, title: this.title.trim() }
      return this.request(() => albumsApi.updateEntry(this.entry.id, body))
    },
    remove() {
      return this.request(() => albumsApi.removeEntry(this.entry.id))
    },
  },
}
</script>

<template>
  <BaseDialog ref="dialog" :title="$t('albumEntry.edit')">
    <div v-if="entry" class="flex flex-col gap-4">
      <img :src="entry.post.thumbnail" alt="" class="size-24 object-cover bg-base-200" />
      <label class="flex flex-col gap-1">
        <span class="text-sm text-app-muted">{{ $t('albumEntry.date') }}</span>
        <input v-model="date" type="date" class="input w-full" />
      </label>
      <label class="flex flex-col gap-1">
        <span class="text-sm text-app-muted">{{ $t('albumEntry.title') }}</span>
        <input v-model="title" class="input w-full" maxlength="50" @keyup.enter="save" />
      </label>
      <ErrorText :message="error" />
    </div>
    <template #actions>
      <BaseButton
        :title="$t('albumEntry.remove')"
        variant="error"
        outline
        class="mr-auto"
        :disabled="busy"
        @click="remove"
      >
        <AppIcon name="trash" />
        <span class="max-sm:hidden">{{ $t('albumEntry.remove') }}</span>
      </BaseButton>
      <BaseButton :title="$t('common.cancel')" @click="$refs.dialog.close()">
        <AppIcon name="cross" />
        <span class="max-sm:hidden">{{ $t('common.cancel') }}</span>
      </BaseButton>
      <BaseButton :title="$t('common.save')" variant="primary" :disabled="busy" @click="save">
        <AppIcon name="disk" />
        <span class="max-sm:hidden">{{ $t('common.save') }}</span>
      </BaseButton>
    </template>
  </BaseDialog>
</template>

<script>
import ErrorText from '@core/components/ErrorText.vue'
import asyncActionMixin from '@core/mixins/asyncActionMixin.js'
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import albumsApi from '@/api/albums.js'
import { t } from '@/i18n.js'

export default {
  name: 'EntryDialog',
  mixins: [asyncActionMixin],
  components: { AppIcon, BaseButton, BaseDialog, ErrorText },
  emits: ['saved'],
  data() {
    return {
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
      this.error = null
      this.$refs.dialog.open()
    },
    async request(action) {
      const album = await this.runAction(action, t('albumEntry.saveFailed'))
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

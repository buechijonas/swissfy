<template>
  <BaseDialog ref="dialog" title="Eintrag bearbeiten">
    <div v-if="entry" class="flex flex-col gap-4">
      <img :src="entry.post.thumbnail" alt="" class="size-24 object-cover bg-base-200" />
      <label class="flex flex-col gap-1">
        <span class="text-sm text-app-muted">Datum (optional)</span>
        <input v-model="date" type="date" class="input w-full" />
      </label>
      <label class="flex flex-col gap-1">
        <span class="text-sm text-app-muted">Titel (optional)</span>
        <input v-model="title" class="input w-full" maxlength="50" @keyup.enter="save" />
      </label>
      <ErrorText :message="error" />
    </div>
    <template #actions>
      <BaseButton
        title="Entfernen"
        variant="error"
        outline
        class="mr-auto"
        :disabled="busy"
        @click="remove"
      >
        <AppIcon name="trash" />
        <span class="max-sm:hidden">Entfernen</span>
      </BaseButton>
      <BaseButton title="Abbrechen" @click="$refs.dialog.close()">
        <AppIcon name="cross" />
        <span class="max-sm:hidden">Abbrechen</span>
      </BaseButton>
      <BaseButton title="Speichern" variant="primary" :disabled="busy" @click="save">
        <AppIcon name="disk" />
        <span class="max-sm:hidden">Speichern</span>
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
      const album = await this.runAction(action, 'Eintrag konnte nicht gespeichert werden.')
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

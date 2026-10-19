<template>
  <BaseDialog ref="dialog" title="Eintrag bearbeiten">
    <div v-if="entry" class="flex flex-col gap-4">
      <img :src="entry.post.thumbnail" alt="" class="size-24 object-cover bg-base-200" />
      <label class="flex flex-col gap-1">
        <span class="text-sm text-swissfy-muted">Datum (optional)</span>
        <input v-model="date" type="date" class="input w-full" />
      </label>
      <label class="flex flex-col gap-1">
        <span class="text-sm text-swissfy-muted">Titel (optional)</span>
        <input v-model="title" class="input w-full" maxlength="50" @keyup.enter="save" />
      </label>
      <p v-if="error" class="text-error text-sm">{{ error }}</p>
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
import AppIcon from '@/components/common/AppIcon.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import { apiFetch, extractErrorMessage } from '@/lib/api.js'

export default {
  name: 'EntryDialog',
  components: { AppIcon, BaseButton, BaseDialog },
  emits: ['saved'],
  data() {
    return {
      entry: null,
      date: '',
      title: '',
      busy: false,
      error: null,
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
    async request(method, body) {
      this.busy = true
      this.error = null
      try {
        const response = await apiFetch(`/api/album-entries/${this.entry.id}/`, {
          method,
          body: body && JSON.stringify(body),
        })
        const data = await response.json().catch(() => null)
        if (!response.ok) {
          this.error = extractErrorMessage(data, 'Eintrag konnte nicht gespeichert werden.')
          return
        }
        this.$refs.dialog.close()
        this.$emit('saved', data)
      } finally {
        this.busy = false
      }
    },
    save() {
      return this.request('PATCH', { date: this.date || null, title: this.title.trim() })
    },
    remove() {
      return this.request('DELETE')
    },
  },
}
</script>

<template>
  <BaseDialog ref="dialog" :title="album ? 'Album bearbeiten' : 'Neues Album'">
    <div class="flex flex-col gap-4">
      <input
        v-model="name"
        class="input w-full"
        maxlength="50"
        placeholder="Name"
        @keyup.enter="save"
      />
      <div v-if="preview" class="relative mx-auto w-40">
        <img :src="preview" alt="Titelbild" class="aspect-square w-full rounded-box object-cover" />
        <BaseButton
          variant="error"
          shape="circle"
          size="sm"
          class="absolute top-2 right-2"
          title="Titelbild entfernen"
          @click="removeCover"
        >
          <AppIcon name="trash" alt="Titelbild entfernen" />
        </BaseButton>
      </div>
      <ImageDropzone v-else class="h-40" label="Titelbild wählen" @select="selectCover" />
      <p v-if="error" class="text-error text-sm">{{ error }}</p>
    </div>
    <template #actions>
      <BaseButton
        title="Löschen"
        v-if="album"
        variant="error"
        outline
        class="mr-auto"
        @click="remove"
      >
        <AppIcon name="trash" />
        <span class="max-sm:hidden">Löschen</span>
      </BaseButton>
      <BaseButton title="Abbrechen" @click="$refs.dialog.close()">
        <AppIcon name="cross" />
        <span class="max-sm:hidden">Abbrechen</span>
      </BaseButton>
      <BaseButton
        title="Speichern"
        variant="primary"
        :disabled="!name.trim() || busy"
        @click="save"
      >
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
import ImageDropzone from '@/components/common/ImageDropzone.vue'
import { apiFetch, extractErrorMessage } from '@/lib/api.js'

export default {
  name: 'AlbumDialog',
  components: { AppIcon, BaseButton, BaseDialog, ImageDropzone },
  emits: ['saved', 'delete'],
  data() {
    return {
      album: null,
      name: '',
      cover: undefined,
      preview: null,
      error: null,
      busy: false,
    }
  },
  methods: {
    open(album = null) {
      this.album = album
      this.name = album?.name ?? ''
      this.cover = undefined
      this.preview = album?.cover ?? null
      this.error = null
      this.$refs.dialog.open()
    },
    remove() {
      this.$refs.dialog.close()
      this.$emit('delete')
    },
    selectCover([file]) {
      this.cover = file
      this.preview = URL.createObjectURL(file)
    },
    removeCover() {
      this.cover = null
      this.preview = null
    },
    body() {
      if (this.cover === null) return JSON.stringify({ name: this.name.trim(), cover: null })
      const form = new FormData()
      form.append('name', this.name.trim())
      if (this.cover) form.append('cover', this.cover)
      return form
    },
    async save() {
      if (!this.name.trim() || this.busy) return
      this.busy = true
      this.error = null
      try {
        const url = this.album ? `/api/albums/${this.album.id}/` : '/api/albums/'
        const method = this.album ? 'PATCH' : 'POST'
        const response = await apiFetch(url, { method, body: this.body() })
        const data = await response.json().catch(() => null)
        if (!response.ok) {
          this.error = extractErrorMessage(data, 'Album konnte nicht gespeichert werden.')
          return
        }
        this.$refs.dialog.close()
        this.$emit('saved', data)
      } finally {
        this.busy = false
      }
    },
  },
}
</script>

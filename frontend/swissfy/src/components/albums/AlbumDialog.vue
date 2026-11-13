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
      <div v-if="album?.entries.length" class="flex min-h-0 flex-col gap-2">
        <span class="text-sm text-app-muted">Titelbild (optional)</span>
        <div class="grid max-h-72 grid-cols-3 gap-2 overflow-y-auto">
          <button
            v-for="entry in album.entries"
            :key="entry.id"
            type="button"
            class="relative"
            data-cover
            :aria-pressed="cover === entry.id"
            @click="toggleCover(entry)"
          >
            <img
              :src="entry.post.thumbnail"
              alt=""
              loading="lazy"
              class="aspect-square w-full rounded-box object-cover bg-base-200"
              :class="{ 'opacity-60': cover === entry.id }"
            />
            <span
              class="absolute top-1 right-1 flex size-6 items-center justify-center rounded-full border-2 border-white"
              :class="cover === entry.id ? 'bg-primary text-primary-content' : 'bg-black/30'"
            >
              <AppIcon v-if="cover === entry.id" name="check" size="sm" alt="Titelbild" />
            </span>
          </button>
        </div>
      </div>
      <p v-else-if="album" class="text-sm text-app-muted">
        Füge Posts zur Timeline hinzu, um eines davon als Titelbild zu wählen.
      </p>
      <ErrorText :message="error" />
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
import ErrorText from '@core/components/ErrorText.vue'
import asyncActionMixin from '@core/mixins/asyncActionMixin.js'
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import albumsApi from '@/api/albums.js'

export default {
  name: 'AlbumDialog',
  mixins: [asyncActionMixin],
  components: { AppIcon, BaseButton, BaseDialog, ErrorText },
  emits: ['saved', 'delete'],
  data() {
    return {
      album: null,
      name: '',
      cover: null,
    }
  },
  methods: {
    open(album = null) {
      this.album = album
      this.name = album?.name ?? ''
      this.cover = album?.cover_entry ?? null
      this.error = null
      this.$refs.dialog.open()
    },
    remove() {
      this.$refs.dialog.close()
      this.$emit('delete')
    },
    toggleCover(entry) {
      this.cover = this.cover === entry.id ? null : entry.id
    },
    async save() {
      if (!this.name.trim() || this.busy) return
      const album = await this.runAction(
        () => this.request(this.name.trim()),
        'Album konnte nicht gespeichert werden.',
      )
      if (!album) return
      this.$refs.dialog.close()
      this.$emit('saved', album)
    },
    request(name) {
      if (this.album) return albumsApi.update(this.album.id, { name, cover: this.cover })
      return albumsApi.create({ name })
    },
  },
}
</script>

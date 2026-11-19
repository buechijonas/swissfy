<template>
  <BaseDialog ref="dialog" :title="album ? $t('albumDialog.edit') : $t('albumDialog.new')">
    <div class="flex flex-col gap-4">
      <input
        v-model="name"
        class="input w-full"
        maxlength="50"
        :placeholder="$t('albumDialog.name')"
        @keyup.enter="save"
      />
      <div v-if="album?.entries.length" class="flex min-h-0 flex-col gap-2">
        <span class="text-sm text-app-muted">{{ $t('albumDialog.cover') }}</span>
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
              class="aspect-square w-full rounded-box bg-base-200 object-cover"
              :class="{ 'opacity-60': cover === entry.id }"
            />
            <span
              class="absolute top-1 right-1 flex size-6 items-center justify-center rounded-full border-2 border-white"
              :class="cover === entry.id ? 'bg-primary text-primary-content' : 'bg-black/30'"
            >
              <AppIcon
                v-if="cover === entry.id"
                name="check"
                size="sm"
                :alt="$t('albumDialog.coverAlt')"
              />
            </span>
          </button>
        </div>
      </div>
      <p v-else-if="album" class="text-sm text-app-muted">
        {{ $t('albumDialog.coverHint') }}
      </p>
      <ErrorText :message="action.error" />
    </div>
    <template #actions>
      <BaseButton
        v-if="album"
        :title="$t('common.delete')"
        variant="error"
        outline
        class="mr-auto"
        @click="remove"
      >
        <AppIcon name="trash" />
        <span class="max-sm:hidden">{{ $t('common.delete') }}</span>
      </BaseButton>
      <BaseButton :title="$t('common.cancel')" @click="$refs.dialog.close()">
        <AppIcon name="cross" />
        <span class="max-sm:hidden">{{ $t('common.cancel') }}</span>
      </BaseButton>
      <BaseButton
        :title="$t('common.save')"
        variant="primary"
        :disabled="!name.trim() || action.busy"
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
  name: 'AlbumDialog',
  components: { AppIcon, BaseButton, BaseDialog, ErrorText },
  emits: ['saved', 'delete'],
  data() {
    return {
      action: useAsyncAction(),
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
      this.action.error = null
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
      if (!this.name.trim() || this.action.busy) return
      const album = await this.action.run(
        () => this.request(this.name.trim()),
        t('albumDialog.saveFailed'),
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

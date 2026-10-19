<template>
  <BaseBreadcrumbs :items="breadcrumbs">
    <template v-if="ownAlbum" #actions>
      <AddButton
        label="Zur Timeline"
        :loading="!album"
        icon="rectangle-history-circle-plus"
        @click="$refs.addDialog.open()"
      />
    </template>
  </BaseBreadcrumbs>
  <div
    class="flex flex-col pb-8 px-6 max-h-[calc(100dvh-var(--mobile-chrome-height))] overflow-y-auto lg:max-h-none lg:overflow-y-visible lg:flex-1"
  >
    <div class="mx-auto w-full max-w-150 sm:pt-4 flex flex-col gap-4">
      <BaseCard v-if="!album && !error" class="p-6">
        <div class="flex items-center gap-4">
          <div class="skeleton size-24"></div>
          <div class="skeleton h-6 w-40"></div>
        </div>
      </BaseCard>

      <BaseCard v-else-if="error" class="p-6">
        <p class="text-swissfy-muted">{{ error }}</p>
      </BaseCard>

      <template v-else>
        <BaseCard class="p-6">
          <div class="flex items-center gap-4">
            <img
              v-if="album.cover"
              :src="album.cover"
              alt=""
              class="size-24 shrink-0 rounded-box object-cover"
            />
            <div
              v-else
              class="flex size-24 shrink-0 items-center justify-center rounded-box bg-base-200 text-swissfy-muted"
            >
              <AppIcon name="gallery" class="size-8!" />
            </div>
            <div class="flex-1 min-w-0">
              <h2 class="truncate text-xl font-semibold">{{ album.name }}</h2>
              <RouterLink :to="profileLink" class="text-sm text-swissfy-muted">
                {{ album.owner }}
              </RouterLink>
            </div>
            <BaseButton
              v-if="album.is_own"
              shape="square"
              class="shrink-0"
              title="Bearbeiten"
              @click="$refs.albumDialog.open(album)"
            >
              <AppIcon name="pencil" alt="Bearbeiten" />
            </BaseButton>
          </div>
        </BaseCard>

        <p v-if="actionError" class="text-error text-sm text-center">{{ actionError }}</p>

        <AlbumTimeline
          :entries="album.entries"
          :editable="album.is_own"
          @edit-entry="$refs.entryDialog.open($event)"
        />
      </template>
    </div>
  </div>

  <template v-if="album?.is_own">
    <AlbumDialog ref="albumDialog" @saved="album = $event" @delete="$refs.confirmAlbum.open()" />
    <AddPostsDialog ref="addDialog" :album="album" @saved="album = $event" />
    <EntryDialog ref="entryDialog" @saved="album = $event" />
    <ConfirmDialog
      ref="confirmAlbum"
      message="Album löschen? Die Posts selbst bleiben erhalten."
      @confirm="deleteAlbum"
    />
  </template>
  <BaseFooter />
</template>

<script>
import { RouterLink } from 'vue-router'
import AddPostsDialog from '@/components/albums/AddPostsDialog.vue'
import AlbumDialog from '@/components/albums/AlbumDialog.vue'
import AlbumTimeline from '@/components/albums/AlbumTimeline.vue'
import EntryDialog from '@/components/albums/EntryDialog.vue'
import AddButton from '@/components/common/AddButton.vue'
import AppIcon from '@/components/common/AppIcon.vue'
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import { apiFetch } from '@/lib/api.js'
import { useAuthStore } from '@/stores/auth.js'

export default {
  name: 'AlbumView',
  components: {
    RouterLink,
    AddPostsDialog,
    AlbumDialog,
    AlbumTimeline,
    EntryDialog,
    AddButton,
    AppIcon,
    BaseBreadcrumbs,
    BaseButton,
    BaseCard,
    BaseFooter,
    ConfirmDialog,
  },
  data() {
    return {
      album: null,
      error: null,
      actionError: null,
    }
  },
  computed: {
    username() {
      return this.$route.params.username
    },
    ownAlbum() {
      if (this.error) return false
      if (this.album) return this.album.is_own
      return this.username === useAuthStore().user?.username
    },
    profileLink() {
      return `/profile/${encodeURIComponent(this.username)}`
    },
    breadcrumbs() {
      return [
        { label: this.username, to: this.profileLink },
        { label: 'Alben', to: `${this.profileLink}?tab=albums` },
        { label: this.album?.name ?? 'Album' },
      ]
    },
  },
  watch: {
    '$route.params.id': {
      immediate: true,
      handler(id) {
        if (id) this.load()
      },
    },
  },
  methods: {
    async load() {
      this.error = null
      const response = await apiFetch(`/api/albums/${this.$route.params.id}/`).catch(() => null)
      if (response?.ok) {
        this.album = await response.json()
      } else {
        this.album = null
        this.error =
          response?.status === 404 ? 'Album nicht gefunden.' : 'Album konnte nicht geladen werden.'
      }
    },
    async deleteAlbum() {
      const response = await apiFetch(`/api/albums/${this.album.id}/`, { method: 'DELETE' })
      if (response.ok) {
        this.$router.replace(`${this.profileLink}?tab=albums`)
      } else {
        this.actionError = 'Album konnte nicht gelöscht werden.'
      }
    },
  },
}
</script>

<template>
  <BaseBreadcrumbs :items="breadcrumbs">
    <template v-if="ownAlbum" #actions>
      <AddButton
        :label="$t('album.addToTimeline')"
        :loading="!album"
        icon="rectangle-history-circle-plus"
        @click="$refs.addDialog.open()"
      />
    </template>
  </BaseBreadcrumbs>
  <div
    class="flex max-h-[calc(100dvh-var(--mobile-chrome-height))] flex-col overflow-y-auto px-6 pb-8 lg:max-h-none lg:flex-1 lg:overflow-y-visible"
  >
    <div class="mx-auto flex w-full max-w-150 flex-col gap-4 sm:pt-4">
      <BaseCard v-if="!album && !error" class="p-6">
        <div class="flex items-center gap-4">
          <div class="size-24 skeleton"></div>
          <div class="h-6 w-40 skeleton"></div>
        </div>
      </BaseCard>

      <BaseCard v-else-if="error" class="p-6">
        <p class="text-app-muted">{{ error }}</p>
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
              class="flex size-24 shrink-0 items-center justify-center rounded-box bg-base-200 text-app-muted"
            >
              <AppIcon name="gallery" class="size-8!" />
            </div>
            <div class="min-w-0 flex-1">
              <h2 class="truncate text-xl font-semibold">{{ album.name }}</h2>
              <RouterLink :to="profileLink" class="text-sm text-app-muted">
                {{ album.owner }}
              </RouterLink>
            </div>
            <BaseButton
              v-if="album.is_own"
              shape="square"
              class="shrink-0"
              :title="$t('common.edit')"
              @click="$refs.albumDialog.open(album)"
            >
              <AppIcon name="pencil" :alt="$t('common.edit')" />
            </BaseButton>
          </div>
        </BaseCard>

        <ErrorText :message="actionError" class="text-center" />

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
    <ConfirmDialog ref="confirmAlbum" :message="$t('album.deleteMessage')" @confirm="deleteAlbum" />
  </template>
  <BaseFooter />
</template>

<script>
import { mapStores } from 'pinia'
import { RouterLink } from 'vue-router'
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import BaseCard from '@core/components/BaseCard.vue'
import ErrorText from '@core/components/ErrorText.vue'
import albumsApi from '@/api/albums.js'
import AddPostsDialog from '@/components/albums/AddPostsDialog.vue'
import AlbumDialog from '@/components/albums/AlbumDialog.vue'
import AlbumTimeline from '@/components/albums/AlbumTimeline.vue'
import EntryDialog from '@/components/albums/EntryDialog.vue'
import AddButton from '@/components/common/AddButton.vue'
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import { t } from '@/i18n.js'
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
    ErrorText,
  },
  data() {
    return {
      album: null,
      error: null,
      actionError: null,
    }
  },
  computed: {
    ...mapStores(useAuthStore),
    username() {
      return this.$route.params.username
    },
    ownAlbum() {
      if (this.error) return false
      if (this.album) return this.album.is_own
      return this.username === this.authStore.user?.username
    },
    profileLink() {
      return `/profile/${encodeURIComponent(this.username)}`
    },
    breadcrumbs() {
      return [
        { label: this.username, to: this.profileLink },
        { label: t('album.albums'), to: `${this.profileLink}?tab=albums` },
        { label: this.album?.name ?? t('album.album') },
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
      try {
        this.album = await albumsApi.get(this.$route.params.id)
      } catch (error) {
        this.album = null
        this.error = error.status === 404 ? t('album.notFound') : t('album.loadFailed')
      }
    },
    async deleteAlbum() {
      try {
        await albumsApi.remove(this.album.id)
        this.$router.replace(`${this.profileLink}?tab=albums`)
      } catch {
        this.actionError = t('album.deleteFailed')
      }
    },
  },
}
</script>

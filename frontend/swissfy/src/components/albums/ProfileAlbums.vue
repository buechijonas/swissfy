<template>
  <BaseCard class="p-4 border-t-0">
    <ErrorText v-if="error" :message="error" class="text-center" />
    <div v-else-if="!albums" class="grid grid-cols-2 gap-4 sm:grid-cols-3">
      <div v-for="n in 3" :key="n" class="skeleton aspect-square rounded-box"></div>
    </div>
    <p v-else-if="!albums.length && !editable" class="text-app-muted">Noch keine Alben.</p>
    <div
      v-else
      class="grid grid-cols-2 gap-4 sm:grid-cols-3"
      @pointerup="endDrag"
      @pointercancel="cancelDrag"
      @pointerleave="cancelDrag"
    >
      <button
        v-if="editable"
        type="button"
        class="group flex flex-col gap-2 text-left"
        title="Neues Album"
        @click="$refs.dialog.open()"
      >
        <span
          class="flex aspect-square w-full items-center justify-center rounded-box border-2 border-dashed border-app-border bg-base-200 text-app-muted transition-colors group-hover:border-primary group-hover:text-primary"
        >
          <AppIcon name="plus" class="size-8!" />
        </span>
        <span class="text-sm font-medium text-app-muted">Neues Album</span>
      </button>
      <div
        v-for="album in shownAlbums"
        :key="album.id"
        class="relative"
        :class="{ 'opacity-50': draggingId === album.id }"
        @pointerenter="dragOver(album)"
      >
        <RouterLink
          :to="`/profile/${encodeURIComponent(username)}/albums/${album.id}`"
          class="flex flex-col gap-2"
        >
          <span class="block aspect-square overflow-hidden rounded-box bg-base-200">
            <img
              v-if="album.cover"
              :src="album.cover"
              alt=""
              class="size-full object-cover transition-transform hover:scale-105"
              loading="lazy"
            />
            <span v-else class="flex size-full items-center justify-center text-app-muted">
              <AppIcon name="gallery" class="size-8!" />
            </span>
          </span>
          <span class="truncate text-sm font-medium">{{ album.name }}</span>
        </RouterLink>
        <button
          v-if="editable && albums.length > 1"
          type="button"
          class="btn btn-circle btn-sm absolute top-2 right-2 border-0 bg-black/50 text-white shadow-none cursor-grab touch-none"
          title="Verschieben"
          v-grab="() => startDrag(album)"
        >
          <AppIcon name="menu-burger" alt="Verschieben" size="sm" />
        </button>
      </div>
    </div>
    <ErrorText :message="orderError" class="mt-2 text-center" />
    <AlbumDialog v-if="editable" ref="dialog" @saved="addAlbum" />
  </BaseCard>
</template>

<script>
import ErrorText from '@core/components/ErrorText.vue'
import { RouterLink } from 'vue-router'
import map from 'lodash-es/map'
import AlbumDialog from '@/components/albums/AlbumDialog.vue'
import AppIcon from '@core/components/AppIcon.vue'
import BaseCard from '@core/components/BaseCard.vue'
import albumsApi from '@/api/albums.js'
import grab from '@/directives/grab.js'
import { moveItem, sameOrder } from '@/lib/sortable.js'

export default {
  name: 'ProfileAlbums',
  components: { RouterLink, AlbumDialog, AppIcon, BaseCard, ErrorText },
  directives: { grab },
  props: {
    username: { type: String, required: true },
    editable: { type: Boolean, default: false },
  },
  data() {
    return {
      albums: null,
      order: null,
      draggingId: null,
      error: null,
      orderError: null,
    }
  },
  computed: {
    shownAlbums() {
      return this.order ?? this.albums
    },
  },
  async created() {
    try {
      this.albums = await albumsApi.ofUser(this.username)
    } catch {
      this.error = 'Alben konnten nicht geladen werden.'
    }
  },
  methods: {
    addAlbum(album) {
      this.albums = [album, ...this.albums]
    },
    startDrag(album) {
      this.order = this.albums
      this.draggingId = album.id
    },
    dragOver(album) {
      if (!this.draggingId) return
      this.order = moveItem(this.order, this.draggingId, album.id)
    },
    async endDrag() {
      if (!this.draggingId) return
      this.draggingId = null
      const order = this.order
      if (sameOrder(order, this.albums)) {
        this.order = null
        return
      }
      this.orderError = null
      try {
        this.albums = await albumsApi.reorder(map(order, 'id'))
      } catch {
        this.orderError = 'Reihenfolge konnte nicht gespeichert werden.'
      }
      this.order = null
    },
    cancelDrag() {
      this.draggingId = null
      this.order = null
    },
  },
}
</script>

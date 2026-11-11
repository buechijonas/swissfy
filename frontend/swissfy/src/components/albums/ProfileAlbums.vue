<template>
  <BaseCard class="p-4 border-t-0">
    <p v-if="error" class="text-error text-sm text-center">{{ error }}</p>
    <div v-else-if="!albums" class="grid grid-cols-2 gap-4 sm:grid-cols-3">
      <div v-for="n in 3" :key="n" class="skeleton aspect-square rounded-box"></div>
    </div>
    <p v-else-if="!albums.length && !editable" class="text-swissfy-muted">Noch keine Alben.</p>
    <div v-else class="grid grid-cols-2 gap-4 sm:grid-cols-3">
      <button
        v-if="editable"
        type="button"
        class="group flex flex-col gap-2 text-left"
        title="Neues Album"
        @click="$refs.dialog.open()"
      >
        <span
          class="flex aspect-square w-full items-center justify-center rounded-box border-2 border-dashed border-swissfy-border bg-base-200 text-swissfy-muted transition-colors group-hover:border-primary group-hover:text-primary"
        >
          <AppIcon name="plus" class="size-8!" />
        </span>
        <span class="text-sm font-medium text-swissfy-muted">Neues Album</span>
      </button>
      <div
        v-for="album in shownAlbums"
        :key="album.id"
        :data-album="album.id"
        class="relative"
        :class="{ 'opacity-50': draggingId === album.id }"
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
            <span v-else class="flex size-full items-center justify-center text-swissfy-muted">
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
          @pointerdown="startDrag($event, album)"
          @pointermove="drag"
          @pointerup="endDrag"
          @pointercancel="cancelDrag"
        >
          <AppIcon name="menu-burger" alt="Verschieben" size="sm" />
        </button>
      </div>
    </div>
    <p v-if="orderError" class="text-error text-sm mt-2 text-center">{{ orderError }}</p>
    <AlbumDialog v-if="editable" ref="dialog" @saved="addAlbum" />
  </BaseCard>
</template>

<script>
import { RouterLink } from 'vue-router'
import AlbumDialog from '@/components/albums/AlbumDialog.vue'
import AppIcon from '@/components/common/AppIcon.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import albumsApi from '@/api/albums.js'
import { itemAt, moveItem, sameOrder } from '@/lib/sortable.js'

export default {
  name: 'ProfileAlbums',
  components: { RouterLink, AlbumDialog, AppIcon, BaseCard },
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
    startDrag(event, album) {
      event.currentTarget.setPointerCapture(event.pointerId)
      this.order = this.albums
      this.draggingId = album.id
    },
    drag(event) {
      if (!this.draggingId) return
      this.order = moveItem(this.order, this.draggingId, itemAt(event, 'data-album'))
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
        this.albums = await albumsApi.reorder(order.map((album) => album.id))
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

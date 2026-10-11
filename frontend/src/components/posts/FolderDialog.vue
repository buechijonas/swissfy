<template>
  <BaseDialog ref="dialog" title="In Ordner verschieben">
    <ul class="menu w-full p-0 gap-1">
      <li>
        <button type="button" :class="{ 'menu-active': selected === null }" @click="select(null)">
          Ohne Ordner
        </button>
      </li>
      <li v-for="folder in folders" :key="folder.id">
        <button
          type="button"
          :class="{ 'menu-active': selected === folder.id }"
          @click="select(folder.id)"
        >
          <AppIcon name="folder" />
          {{ folder.name }}
        </button>
      </li>
    </ul>

    <form class="flex gap-2 mt-4" @submit.prevent="createFolder">
      <input v-model="newName" class="input flex-1" maxlength="50" placeholder="Neuer Ordner" />
      <BaseButton type="submit" :disabled="!newName.trim()">
        <AppIcon name="plus" />
        Anlegen
      </BaseButton>
    </form>
    <p v-if="error" class="text-error text-sm mt-2">{{ error }}</p>
  </BaseDialog>
</template>

<script>
import AppIcon from '@/components/common/AppIcon.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import { useFoldersStore } from '@/stores/posts.js'

export default {
  name: 'FolderDialog',
  components: { AppIcon, BaseButton, BaseDialog },
  emits: ['select'],
  data() {
    return {
      selected: null,
      newName: '',
      error: null,
    }
  },
  computed: {
    foldersStore() {
      return useFoldersStore()
    },
    folders() {
      return this.foldersStore.items ?? []
    },
  },
  methods: {
    open(selected) {
      this.selected = selected
      this.newName = ''
      this.error = null
      this.foldersStore.load().catch(() => {
        this.error = 'Ordner konnten nicht geladen werden.'
      })
      this.$refs.dialog.open()
    },
    select(folder) {
      this.$refs.dialog.close()
      if (folder !== this.selected) this.$emit('select', folder)
    },
    async createFolder() {
      this.error = null
      try {
        const folder = await this.foldersStore.create({ name: this.newName.trim() })
        this.select(folder.id)
      } catch (error) {
        this.error = error.message
      }
    },
  },
}
</script>

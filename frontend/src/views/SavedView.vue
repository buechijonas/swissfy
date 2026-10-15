<template>
  <BaseBreadcrumbs :items="breadcrumbs">
    <template #actions>
      <AddButton label="Ordner" @click="openFolderDialog(null)" />
    </template>
  </BaseBreadcrumbs>
  <div
    class="flex flex-col pb-8 px-6 max-sm:pb-0 max-h-[calc(100dvh-var(--mobile-chrome-height))] overflow-y-auto lg:max-h-none lg:overflow-y-visible lg:flex-1"
  >
    <div class="mx-auto w-full max-w-150 pt-4">
      <div class="flex flex-wrap items-center gap-2 mb-4">
        <BaseButton
          v-for="filter in filters"
          :key="filter.value"
          size="sm"
          :variant="activeFolder === filter.value ? 'primary' : 'neutral'"
          :to="{ query: filter.value ? { folder: filter.value } : {} }"
        >
          <AppIcon :name="filter.icon" />
          {{ filter.label }}
        </BaseButton>
      </div>

      <div v-if="currentFolder" class="flex items-center gap-2 mb-4">
        <h3 class="text-xl truncate">{{ currentFolder.name }}</h3>
        <BaseButton size="sm" class="ml-auto" @click="openFolderDialog(currentFolder)">
          <AppIcon name="pencil" />
          Umbenennen
        </BaseButton>
        <DeleteButton @click="$refs.confirm.open()" />
      </div>
      <p v-if="folderError" class="text-error text-sm mb-4">{{ folderError }}</p>

      <PostList
        :key="activeFolder"
        ref="list"
        :url="listUrl"
        folder-picker
        edge-to-edge
        empty-text="Hier ist noch nichts gespeichert."
        @saved-change="onSavedChange"
      />
    </div>
  </div>

  <BaseDialog ref="folderDialog" :title="editedFolder ? 'Ordner umbenennen' : 'Neuer Ordner'">
    <input
      v-model="folderName"
      class="input w-full"
      maxlength="50"
      placeholder="Name"
      @keyup.enter="saveFolder"
    />
    <p v-if="folderError" class="text-error text-sm mt-2">{{ folderError }}</p>
    <template #actions>
      <BaseButton @click="$refs.folderDialog.close()">
        <AppIcon name="cross" />
        Abbrechen
      </BaseButton>
      <BaseButton variant="primary" :disabled="!folderName.trim()" @click="saveFolder">
        <AppIcon name="disk" />
        Speichern
      </BaseButton>
    </template>
  </BaseDialog>
  <ConfirmDialog
    ref="confirm"
    message="Ordner löschen? Die gespeicherten Posts bleiben unter «Ohne Ordner»."
    @confirm="deleteFolder"
  />
  <BaseFooter />
</template>

<script>
import AddButton from '@/components/common/AddButton.vue'
import AppIcon from '@/components/common/AppIcon.vue'
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import DeleteButton from '@/components/common/DeleteButton.vue'
import PostList from '@/components/posts/PostList.vue'
import { useFoldersStore } from '@/stores/posts.js'

export default {
  name: 'SavedView',
  components: {
    AddButton,
    AppIcon,
    BaseBreadcrumbs,
    BaseButton,
    BaseDialog,
    BaseFooter,
    ConfirmDialog,
    DeleteButton,
    PostList,
  },
  data() {
    return {
      breadcrumbs: [{ label: 'Gespeichert', to: '/saved' }],
      editedFolder: null,
      folderName: '',
      folderError: null,
    }
  },
  computed: {
    foldersStore() {
      return useFoldersStore()
    },
    filters() {
      return [
        { value: null, label: 'Alle', icon: 'apps' },
        { value: 'none', label: 'Ohne Ordner', icon: 'bookmark' },
        ...(this.foldersStore.items ?? []).map((folder) => ({
          value: String(folder.id),
          label: folder.name,
          icon: 'folder',
        })),
      ]
    },
    activeFolder() {
      return this.$route.query.folder ?? null
    },
    currentFolder() {
      return this.foldersStore.items?.find((folder) => String(folder.id) === this.activeFolder)
    },
    listUrl() {
      const query = this.activeFolder ? `?folder=${this.activeFolder}` : ''
      return `/api/posts/saved/${query}`
    },
  },
  created() {
    this.foldersStore.load().catch(() => {
      this.folderError = 'Ordner konnten nicht geladen werden.'
    })
  },
  methods: {
    onSavedChange(post, { saved, folder }) {
      const stillListed =
        saved &&
        (!this.activeFolder ||
          (this.activeFolder === 'none' ? folder === null : String(folder) === this.activeFolder))
      if (!stillListed) this.$refs.list.remove(post.id)
    },
    openFolderDialog(folder) {
      this.editedFolder = folder
      this.folderName = folder?.name ?? ''
      this.folderError = null
      this.$refs.folderDialog.open()
    },
    async saveFolder() {
      const name = this.folderName.trim()
      if (!name) return
      try {
        const folder = this.editedFolder
          ? await this.foldersStore.update(this.editedFolder.id, { name })
          : await this.foldersStore.create({ name })
        this.$refs.folderDialog.close()
        this.$router.replace({ query: { folder: folder.id } })
      } catch (error) {
        this.folderError = error.message
      }
    },
    async deleteFolder() {
      try {
        await this.foldersStore.remove(this.currentFolder.id)
        this.$router.replace({ query: {} })
      } catch (error) {
        this.folderError = error.message
      }
    },
  },
}
</script>

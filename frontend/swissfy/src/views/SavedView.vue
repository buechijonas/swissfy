<template>
  <BaseBreadcrumbs :items="breadcrumbs">
    <template #actions>
      <AddButton :label="$t('saved.folder')" @click="openFolderDialog(null)" />
    </template>
  </BaseBreadcrumbs>
  <div
    class="flex max-h-[calc(100dvh-var(--mobile-chrome-height))] flex-col overflow-y-auto px-6 pb-8 max-sm:pb-0 lg:max-h-none lg:flex-1 lg:overflow-y-visible"
  >
    <div class="mx-auto w-full max-w-150 pt-4">
      <div class="mb-4 flex flex-wrap items-center gap-2">
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

      <div v-if="currentFolder" class="mb-4 flex items-center gap-2">
        <h3 class="truncate text-xl">{{ currentFolder.name }}</h3>
        <BaseButton size="sm" class="ml-auto" @click="openFolderDialog(currentFolder)">
          <AppIcon name="pencil" />
          {{ $t('saved.rename') }}
        </BaseButton>
        <DeleteButton @click="$refs.confirm.open()" />
      </div>
      <ErrorText :message="folderError" class="mb-4" />

      <PostList
        :key="activeFolder"
        ref="list"
        :url="listUrl"
        folder-picker
        edge-to-edge
        :empty-text="$t('saved.empty')"
        @saved-change="onSavedChange"
      />
    </div>
  </div>

  <BaseDialog
    ref="folderDialog"
    :title="editedFolder ? $t('saved.renameFolder') : $t('saved.newFolder')"
  >
    <input
      v-model="folderName"
      class="input w-full"
      maxlength="50"
      :placeholder="$t('saved.name')"
      @keyup.enter="saveFolder"
    />
    <ErrorText :message="folderError" class="mt-2" />
    <template #actions>
      <BaseButton @click="$refs.folderDialog.close()">
        <AppIcon name="cross" />
        {{ $t('common.cancel') }}
      </BaseButton>
      <BaseButton variant="primary" :disabled="!folderName.trim()" @click="saveFolder">
        <AppIcon name="disk" />
        {{ $t('common.save') }}
      </BaseButton>
    </template>
  </BaseDialog>
  <ConfirmDialog ref="confirm" :message="$t('saved.deleteMessage')" @confirm="deleteFolder" />
  <BaseFooter />
</template>

<script>
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import ErrorText from '@core/components/ErrorText.vue'
import postsApi from '@/api/posts.js'
import AddButton from '@/components/common/AddButton.vue'
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import DeleteButton from '@/components/common/DeleteButton.vue'
import PostList from '@/components/posts/PostList.vue'
import { t } from '@/i18n.js'
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
    ErrorText,
  },
  data() {
    return {
      editedFolder: null,
      folderName: '',
      folderError: null,
    }
  },
  computed: {
    breadcrumbs() {
      return [{ label: t('saved.title'), to: '/saved' }]
    },
    foldersStore() {
      return useFoldersStore()
    },
    filters() {
      return [
        { value: null, label: t('saved.all'), icon: 'apps' },
        { value: 'none', label: t('saved.noFolder'), icon: 'bookmark' },
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
      return postsApi.savedUrl(this.activeFolder)
    },
  },
  created() {
    this.foldersStore.load().catch(() => {
      this.folderError = t('saved.loadFailed')
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

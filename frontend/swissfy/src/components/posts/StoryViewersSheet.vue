<template>
  <BaseDialog
    ref="dialog"
    :title="$t('story.seenBy')"
    class="modal-bottom sm:modal-middle"
    box-class="h-[80dvh] max-w-150 pb-0"
  >
    <div class="-mx-6 min-h-0 flex-1 overflow-y-auto px-6 pb-6 [&_p]:text-center">
      <UserList
        v-if="storyId"
        :key="storyId"
        :url="viewersUrl"
        :empty-text="$t('story.noViewers')"
        :link-to="(user) => `/profile/${encodeURIComponent(user.username)}`"
      >
        <template #default="{ user }">
          <AppIcon
            v-if="user.liked"
            name="heart-filled"
            :alt="$t('story.liked')"
            class="size-6! text-primary"
          />
        </template>
      </UserList>
    </div>
  </BaseDialog>
</template>

<script>
import AppIcon from '@core/components/AppIcon.vue'
import storiesApi from '@/api/stories.js'
import BaseDialog from '@/components/common/BaseDialog.vue'
import UserList from '@/components/common/UserList.vue'

export default {
  name: 'StoryViewersSheet',
  components: { AppIcon, BaseDialog, UserList },
  data() {
    return { storyId: null }
  },
  computed: {
    viewersUrl() {
      return storiesApi.viewersUrl(this.storyId)
    },
  },
  methods: {
    open(storyId) {
      this.storyId = storyId
      this.$refs.dialog.open()
    },
    close() {
      this.$refs.dialog.close()
    },
  },
}
</script>

<template>
  <BaseCard
    tag="article"
    :inset="!edgeToEdge"
    :class="{
      'max-sm:border-y-0': edgeToEdge,
      'cursor-pointer': !detail,
      'relative max-w-full border-0! bg-black!': reel,
      relative: !hasMedia,
      'select-none': tapPending,
    }"
    class="touch-manipulation"
    @click="onCardClick"
  >
    <div
      :class="{ relative: overlay }"
      @mousemove="showControls"
      @touchstart.passive="showControls"
    >
      <AuthorHeader
        :author="post.author"
        :overlay="overlay"
        :class="{ 'absolute inset-x-0 top-0 z-1': overlay }"
        @click.stop
      >
        <template v-if="!reel">
          <BaseButton
            v-if="folderPicker && post.saved"
            outline
            shape="square"
            size="sm"
            :disabled="busy"
            title="In Ordner verschieben"
            @click="$refs.folderDialog.open(post.saved_folder)"
          >
            <AppIcon name="folder" alt="In Ordner verschieben" />
          </BaseButton>
          <BaseButton
            v-if="post.can_report"
            outline
            size="sm"
            :disabled="busy || post.reported"
            @click="report"
          >
            <AppIcon name="flag" />
            {{ post.reported ? 'Gemeldet' : 'Melden' }}
          </BaseButton>
          <PostAction
            v-if="post.is_own && !moderation"
            icon="pencil"
            title="Bearbeiten"
            @select="$refs.edit.open()"
          />
        </template>
      </AuthorHeader>

      <template v-if="!post.video">
        <p v-if="post.hidden" class="px-4 pt-3 text-xs font-bold text-error">
          Öffentlich verborgen
        </p>
        <PostText
          v-if="post.text"
          :parts="post.text_parts"
          class="px-4 py-3 whitespace-pre-line break-words"
        />
      </template>

      <PostVideo
        v-if="post.video || post.video_status"
        ref="player"
        :post="post"
        :detail="detail"
        :reel="reel"
        :overlay="overlay"
        @tap="tap(togglePlay)"
      >
        <HeartBurst ref="heart" />
      </PostVideo>
    </div>
    <p v-if="post.video && post.hidden" class="px-4 pt-3 text-xs font-bold text-error">
      Öffentlich verborgen
    </p>
    <PostText
      v-if="post.video && !overlay && post.text"
      :parts="post.text_parts"
      class="px-4 pt-3 whitespace-pre-line break-words"
    />

    <PostImages v-if="post.images.length" :images="post.images">
      <HeartBurst ref="heart" />
    </PostImages>

    <HeartBurst v-if="!hasMedia" ref="heart" />

    <PostActions
      v-if="!moderation"
      :post="post"
      :reel="reel"
      :busy="busy"
      :commentable="hasCommentSheet"
      :has-menu="hasMenu"
      @like="toggleLike"
      @comments="$refs.comments.open()"
      @repost="toggleRepost"
      @save="toggleSave"
      @menu="$refs.menu.open()"
    />
    <ErrorText :message="error" class="px-4 pb-3" />

    <BaseDialog
      v-if="reel && hasMenu"
      ref="menu"
      title="Seed"
      class="modal-bottom sm:modal-middle"
      @click.stop
    >
      <div class="flex flex-col gap-2">
        <BaseButton v-if="post.is_own && !moderation" block @click="editFromMenu">
          <AppIcon name="pencil" />
          Seed bearbeiten
        </BaseButton>
        <BaseButton
          v-if="post.can_report"
          block
          :disabled="busy || post.reported"
          @click="reportFromMenu"
        >
          <AppIcon name="shield-exclamation" />
          {{ post.reported ? 'Gemeldet' : 'Seed melden' }}
        </BaseButton>
      </div>
    </BaseDialog>
    <PostEditDialog
      v-if="post.is_own && !moderation"
      ref="edit"
      :post="post"
      @click.stop
      @updated="$emit('update', $event)"
      @deleted="$emit('deleted', post.id)"
    />
    <CommentSheet
      v-if="hasCommentSheet"
      ref="comments"
      :post-id="post.id"
      @click.stop
      @created="refresh"
      @deleted="refresh"
    />
    <FolderDialog v-if="folderPicker" ref="folderDialog" @click.stop @select="moveToFolder" />
  </BaseCard>
</template>

<script>
import ErrorText from '@core/components/ErrorText.vue'
import asyncActionMixin from '@core/mixins/asyncActionMixin.js'
import doubleTapMixin from '@/mixins/doubleTapMixin.js'
import { mapStores } from 'pinia'
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import BaseCard from '@core/components/BaseCard.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import AuthorHeader from '@/components/posts/AuthorHeader.vue'
import CommentSheet from '@/components/posts/CommentSheet.vue'
import FolderDialog from '@/components/posts/FolderDialog.vue'
import HeartBurst from '@/components/posts/HeartBurst.vue'
import PostAction from '@/components/posts/PostAction.vue'
import PostActions from '@/components/posts/PostActions.vue'
import PostEditDialog from '@/components/posts/PostEditDialog.vue'
import PostImages from '@/components/posts/PostImages.vue'
import PostText from '@/components/posts/PostText.vue'
import PostVideo from '@/components/posts/PostVideo.vue'
import postsApi from '@/api/posts.js'
import { useAuthStore } from '@/stores/auth.js'

export default {
  name: 'PostCard',
  mixins: [asyncActionMixin, doubleTapMixin],
  components: {
    AppIcon,
    AuthorHeader,
    BaseButton,
    BaseCard,
    BaseDialog,
    CommentSheet,
    FolderDialog,
    HeartBurst,
    PostAction,
    PostActions,
    PostEditDialog,
    PostImages,
    PostText,
    PostVideo,
    ErrorText,
  },
  props: {
    post: { type: Object, required: true },
    detail: { type: Boolean, default: false },
    folderPicker: { type: Boolean, default: false },
    edgeToEdge: { type: Boolean, default: false },
    moderation: { type: Boolean, default: false },
    reel: { type: Boolean, default: false },
  },
  emits: ['update', 'deleted', 'saved-change'],
  data() {
    return {}
  },
  computed: {
    ...mapStores(useAuthStore),
    hasMedia() {
      return Boolean(this.post.video || this.post.video_status || this.post.images.length)
    },
    overlay() {
      return this.reel && Boolean(this.post.video)
    },
    hasCommentSheet() {
      return this.authStore.isAuthenticated && !this.moderation && (this.reel || !this.detail)
    },
    hasMenu() {
      return (this.post.is_own && !this.moderation) || this.post.can_report
    },
  },
  methods: {
    onCardClick() {
      if (this.moderation) {
        if (!this.detail) this.$router.push(`/moderation/posts/${this.post.id}`)
        return
      }
      this.tap(this.hasCommentSheet && !this.reel ? this.openComments : null)
    },
    doubleTap() {
      if (this.moderation) return
      this.$refs.heart.show()
      if (!this.post.liked) this.toggleLike()
    },
    openComments() {
      this.$refs.comments.open()
    },
    togglePlay() {
      this.$refs.player.toggle()
    },
    showControls() {
      if (this.post.video) this.$refs.player.showControls()
    },
    async run(request) {
      if (!this.authStore.isAuthenticated) {
        this.$router.push('/login')
        return null
      }
      const post = await this.runAction(request, 'Aktion fehlgeschlagen.')
      if (post) this.$emit('update', post)
      return post
    },
    toggleLike() {
      const { id, liked } = this.post
      return this.run(() => (liked ? postsApi.unlike(id) : postsApi.like(id)))
    },
    toggleRepost() {
      const { id, reposted } = this.post
      return this.run(() => (reposted ? postsApi.unrepost(id) : postsApi.repost(id)))
    },
    toggleSave() {
      const { id, saved } = this.post
      return this.changeSaved(() => (saved ? postsApi.unsave(id) : postsApi.save(id, null)))
    },
    moveToFolder(folder) {
      return this.changeSaved(() => postsApi.save(this.post.id, folder))
    },
    async changeSaved(request) {
      const post = await this.run(request)
      if (post) this.$emit('saved-change', { saved: post.saved, folder: post.saved_folder })
    },
    report() {
      return this.run(() => postsApi.report(this.post.id))
    },
    refresh() {
      return this.run(() => postsApi.get(this.post.id))
    },
    editFromMenu() {
      this.$refs.menu.close()
      this.$refs.edit.open()
    },
    async reportFromMenu() {
      await this.report()
      this.$refs.menu.close()
    },
  },
}
</script>

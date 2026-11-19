<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div
    class="flex max-h-[calc(100dvh-var(--mobile-chrome-height))] flex-1 flex-col overflow-y-auto bg-base-100 px-6 pb-8 lg:max-h-none lg:overflow-y-visible"
  >
    <div class="flex w-full flex-1 flex-col pt-4">
      <template v-if="kind === 'story'">
        <StoryImagePicker v-model="storyImage" :caption="text" />
        <textarea
          v-model="text"
          class="textarea mt-4 h-20 w-full resize-none"
          :maxlength="maxLength"
          :placeholder="$t('upload.storyText')"
        ></textarea>
        <p class="mt-2 text-right text-xs text-app-muted">{{ text.length }} / {{ maxLength }}</p>
      </template>

      <template v-else>
        <PostMediaPicker v-model:images="images" v-model:video="video" />

        <textarea
          v-model="text"
          class="textarea mt-4 h-28 w-full resize-none"
          :maxlength="maxLength"
          :placeholder="$t('upload.postText')"
        ></textarea>
        <div class="mt-2 flex items-start gap-2">
          <div class="flex min-w-0 flex-1 flex-wrap gap-1">
            <span
              v-for="hashtag in hashtags"
              :key="hashtag"
              class="badge badge-soft badge-sm badge-primary"
            >
              #{{ hashtag }}
            </span>
          </div>
          <p class="shrink-0 text-xs text-app-muted">{{ text.length }} / {{ maxLength }}</p>
        </div>
      </template>

      <div class="mt-4">
        <VisibilityPicker
          v-model:visibility="visibility"
          v-model:groups="selectedGroups"
          :allow-global="kind === 'feed'"
        />
      </div>

      <ErrorText :message="error" class="mt-4" />

      <label class="mt-4 flex items-center gap-3 text-sm">
        <input v-model="acceptedTerms" type="checkbox" class="size-8 shrink-0 accent-primary" />
        <i18n-t
          :keypath="kind === 'story' ? 'upload.confirmStory' : 'upload.confirmPost'"
          tag="span"
        >
          <template #terms>
            <a :href="termsUrl" target="_blank" rel="noopener" class="link text-primary">{{
              $t('upload.terms')
            }}</a>
          </template>
        </i18n-t>
      </label>
      <p
        v-if="quota && kind === 'feed'"
        class="mt-4 text-sm"
        :class="quota.remaining ? 'text-app-muted' : 'text-error'"
      >
        {{
          quota.remaining
            ? $t('upload.quotaLeft', { remaining: quota.remaining, limit: quota.limit })
            : $t('upload.quotaUsed', { limit: quota.limit })
        }}
      </p>

      <div class="mt-auto flex justify-end gap-2 pt-6">
        <BaseButton :disabled="sending" @click="leave">
          <AppIcon name="cross" />
          {{ $t('common.cancel') }}
        </BaseButton>
        <BaseButton variant="primary" :disabled="!canSubmit" @click="submit">
          <span v-if="sending" class="loading loading-sm loading-spinner"></span>
          <AppIcon v-else name="paper-plane-top" />
          {{ sending ? $t('upload.posting') : $t('upload.post') }}
        </BaseButton>
      </div>
    </div>
  </div>
  <BaseFooter />
</template>

<script>
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import ErrorText from '@core/components/ErrorText.vue'
import postsApi from '@/api/posts.js'
import storiesApi from '@/api/stories.js'
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import PostMediaPicker from '@/components/posts/PostMediaPicker.vue'
import StoryImagePicker from '@/components/posts/StoryImagePicker.vue'
import VisibilityPicker from '@/components/posts/VisibilityPicker.vue'
import { legalUrl } from '@/data/footer.js'
import { t } from '@/i18n.js'
import { extractHashtags } from '@/lib/hashtags.js'
import { pageTitle } from '@/lib/title.js'
import { useGroupsStore } from '@/stores/posts.js'

const MAX_LENGTH = 500
const MAX_STORY_LENGTH = 200

export default {
  name: 'UploadView',
  components: {
    AppIcon,
    BaseBreadcrumbs,
    BaseButton,
    BaseFooter,
    PostMediaPicker,
    StoryImagePicker,
    VisibilityPicker,
    ErrorText,
  },
  data() {
    return {
      text: '',
      images: [],
      storyImage: null,
      video: null,
      quota: null,
      visibility: 'public',
      selectedGroups: [],
      acceptedTerms: false,
      sending: false,
      error: null,
    }
  },
  computed: {
    termsUrl() {
      return legalUrl('terms')
    },
    kind() {
      return this.$route.params.kind
    },
    breadcrumbs() {
      return [{ label: pageTitle(this.$route), to: this.$route.path }]
    },
    maxLength() {
      return this.kind === 'story' ? MAX_STORY_LENGTH : MAX_LENGTH
    },
    hashtags() {
      return extractHashtags(this.text)
    },
    canSubmit() {
      const hasAudience = this.visibility !== 'groups' || this.selectedGroups.length
      if (this.sending || !this.acceptedTerms || !hasAudience) return false
      if (this.kind === 'story') return Boolean(this.storyImage)
      const hasContent = this.text.trim() !== '' || this.images.length > 0 || Boolean(this.video)
      return hasContent && this.quota?.remaining !== 0
    },
  },
  mounted() {
    useGroupsStore()
      .load()
      .catch(() => {})
    if (this.kind === 'feed') this.loadQuota()
  },
  methods: {
    leave() {
      if (this.$router.options.history.state.back) {
        this.$router.back()
      } else {
        this.$router.replace(this.kind === 'story' ? '/profile' : '/')
      }
    },
    async loadQuota() {
      try {
        this.quota = await postsApi.quota()
      } catch {
        this.quota = null
      }
    },
    form() {
      const body = new FormData()
      body.append('text', this.text.trim())
      body.append('visibility', this.visibility)
      if (this.visibility === 'groups') {
        for (const id of this.selectedGroups) body.append('groups', id)
      }
      if (this.kind === 'story') {
        body.append('image', this.storyImage.blob, 'story')
      } else {
        this.images.forEach((image) => body.append('images', image.blob, 'image'))
        if (this.video) body.append('video', this.video.file)
      }
      return body
    },
    async submit() {
      if (!this.canSubmit) return
      const story = this.kind === 'story'
      const fallback = story ? t('upload.storyFailed') : t('upload.postFailed')
      this.sending = true
      this.error = null
      try {
        await (story ? storiesApi.create(this.form()) : postsApi.create(this.form()))
        this.leave()
      } catch (error) {
        this.error = error.detail ?? fallback
        if (error.status === 429) this.loadQuota()
      } finally {
        this.sending = false
      }
    },
  },
}
</script>

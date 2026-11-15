<template>
  <BaseDialog
    ref="dialog"
    :title="step === 'select' ? $t('albumPosts.choose') : $t('albumPosts.setDate')"
  >
    <div v-if="step === 'select'" class="min-h-0 overflow-y-auto max-h-96">
      <p v-if="!available.length && !loading && !next" class="text-app-muted">
        {{ $t('albumPosts.empty') }}
      </p>
      <div class="grid grid-cols-3 gap-2">
        <button
          v-for="post in available"
          :key="post.id"
          type="button"
          class="relative"
          data-pick
          :aria-pressed="isSelected(post)"
          @click="toggle(post)"
        >
          <img
            :src="post.thumbnail"
            alt=""
            loading="lazy"
            class="aspect-square w-full rounded-box object-cover bg-base-200"
            :class="{ 'opacity-60': isSelected(post) }"
          />
          <span
            class="absolute top-1 right-1 flex size-6 items-center justify-center rounded-full border-2 border-white"
            :class="isSelected(post) ? 'bg-primary text-primary-content' : 'bg-black/30'"
          >
            <AppIcon
              v-if="isSelected(post)"
              name="check"
              size="sm"
              :alt="$t('albumPosts.selected')"
            />
          </span>
        </button>
      </div>
      <div v-if="loading" class="grid grid-cols-3 gap-1 mt-1">
        <div v-for="n in 3" :key="n" class="skeleton aspect-square"></div>
      </div>
      <BaseButton v-else-if="next" size="sm" block class="mt-2" @click="loadPosts">
        <AppIcon name="down" />
        {{ $t('albumPosts.loadMore') }}
      </BaseButton>
    </div>

    <ul v-else class="flex min-h-0 flex-col gap-3 overflow-y-auto max-h-96">
      <li v-for="item in selected" :key="item.post.id" class="flex items-center gap-3">
        <img :src="item.post.thumbnail" alt="" class="size-16 shrink-0 object-cover bg-base-200" />
        <div class="flex flex-1 min-w-0 flex-col gap-1">
          <input
            v-model="item.date"
            type="date"
            class="input input-sm w-full"
            :aria-label="$t('albumPosts.date')"
          />
          <input
            v-model="item.title"
            class="input input-sm w-full"
            maxlength="50"
            :placeholder="$t('albumPosts.title')"
          />
        </div>
      </li>
    </ul>

    <ErrorText :message="error" class="mt-2" />

    <template #actions>
      <template v-if="step === 'select'">
        <BaseButton :title="$t('common.cancel')" @click="$refs.dialog.close()">
          <AppIcon name="cross" />
          <span class="max-sm:hidden">{{ $t('common.cancel') }}</span>
        </BaseButton>
        <BaseButton
          :title="$t('common.next')"
          variant="primary"
          :disabled="!selected.length"
          @click="step = 'dates'"
        >
          <AppIcon name="angle-right" />
          <span class="max-sm:hidden">{{ $t('common.next') }}</span> ({{ selected.length }})
        </BaseButton>
      </template>
      <template v-else>
        <BaseButton :title="$t('common.back')" @click="step = 'select'">
          <AppIcon name="angle-left" />
          <span class="max-sm:hidden">{{ $t('common.back') }}</span>
        </BaseButton>
        <BaseButton :title="$t('albumPosts.add')" variant="primary" :disabled="busy" @click="save">
          <AppIcon name="disk" />
          <span class="max-sm:hidden">{{ $t('albumPosts.add') }}</span>
        </BaseButton>
      </template>
    </template>
  </BaseDialog>
</template>

<script>
import ErrorText from '@core/components/ErrorText.vue'
import asyncActionMixin from '@core/mixins/asyncActionMixin.js'
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import albumsApi from '@/api/albums.js'
import api, { nextPage } from '@core/api/client.js'
import postsApi from '@/api/posts.js'
import { t } from '@/i18n.js'

export default {
  name: 'AddPostsDialog',
  mixins: [asyncActionMixin],
  components: { AppIcon, BaseButton, BaseDialog, ErrorText },
  props: {
    album: { type: Object, required: true },
  },
  emits: ['saved'],
  data() {
    return {
      step: 'select',
      posts: [],
      next: null,
      selected: [],
      loading: false,
    }
  },
  computed: {
    available() {
      const added = new Set(this.album.entries.map((entry) => entry.post.id))
      return this.posts.filter((post) => !added.has(post.id))
    },
  },
  methods: {
    open() {
      this.step = 'select'
      this.selected = []
      this.posts = []
      this.error = null
      this.next = postsApi.userPostsUrl(this.album.owner, { media: 1 })
      this.loadPosts()
      this.$refs.dialog.open()
    },
    async loadPosts() {
      if (this.loading || !this.next) return
      this.loading = true
      try {
        const data = await api.get(this.next)
        this.posts.push(...data.results)
        this.next = nextPage(data.next)
      } catch {
        this.error = t('albumPosts.loadFailed')
      } finally {
        this.loading = false
      }
    },
    isSelected(post) {
      return this.selected.some((item) => item.post.id === post.id)
    },
    toggle(post) {
      this.selected = this.isSelected(post)
        ? this.selected.filter((item) => item.post.id !== post.id)
        : [...this.selected, { post, date: '', title: '' }]
    },
    async save() {
      const entries = this.selected.map((item) => ({
        post: item.post.id,
        date: item.date || null,
        title: item.title.trim(),
      }))
      const album = await this.runAction(
        () => albumsApi.addEntries(this.album.id, entries),
        t('albumPosts.addFailed'),
      )
      if (!album) return
      this.$refs.dialog.close()
      this.$emit('saved', album)
    },
  },
}
</script>

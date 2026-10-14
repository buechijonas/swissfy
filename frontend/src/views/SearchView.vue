<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div
    class="flex flex-col pb-8 px-6 max-h-[calc(100dvh-96px)] overflow-y-auto lg:max-h-none lg:overflow-y-visible lg:flex-1"
  >
    <div class="mx-auto w-full max-w-150 pt-4">
      <label class="input w-full mb-4 max-lg:hidden">
        <AppIcon name="search" class="text-swissfy-muted" />
        <input
          v-model="term"
          type="search"
          class="grow"
          :placeholder="placeholder"
          autocomplete="off"
        />
      </label>
      <HashtagList :query="query" />
      <UserList
        v-if="!query.startsWith('#')"
        :query="query"
        :link-to="(user) => `/profile/${encodeURIComponent(user.username)}`"
      />
    </div>
  </div>
  <SearchButton @click="openDialog" />
  <BaseDialog ref="dialog" title="Suchen">
    <form id="search-dialog-form" @submit.prevent="submitDialog">
      <label class="input w-full">
        <AppIcon name="search" class="text-swissfy-muted" />
        <input
          ref="dialogInput"
          v-model="draft"
          type="search"
          class="grow"
          :placeholder="placeholder"
          autocomplete="off"
          enterkeyhint="search"
        />
      </label>
    </form>
    <template #actions>
      <BaseButton @click="$refs.dialog.close()">
        <AppIcon name="cross" />
        Abbrechen
      </BaseButton>
      <BaseButton type="submit" form="search-dialog-form" variant="primary">
        <AppIcon name="search" />
        Suchen
      </BaseButton>
    </template>
  </BaseDialog>
  <BaseFooter />
</template>

<script>
import AppIcon from '@/components/common/AppIcon.vue'
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import SearchButton from '@/components/common/SearchButton.vue'
import UserList from '@/components/common/UserList.vue'
import HashtagList from '@/components/posts/HashtagList.vue'

const DEBOUNCE_MS = 300
const MIN_QUERY_LENGTH = 2

export default {
  name: 'SearchView',
  components: {
    AppIcon,
    BaseBreadcrumbs,
    BaseButton,
    BaseDialog,
    BaseFooter,
    HashtagList,
    SearchButton,
    UserList,
  },
  data() {
    return {
      breadcrumbs: [{ label: 'Suchen', to: '/search' }],
      placeholder: 'Nach Benutzern oder #Hashtags suchen',
      term: this.$route.query.q ?? '',
      draft: '',
    }
  },
  computed: {
    query() {
      const query = (this.$route.query.q ?? '').trim()
      return query.length >= MIN_QUERY_LENGTH ? query : ''
    },
  },
  watch: {
    term(term) {
      clearTimeout(this.timer)
      if (term.trim() === (this.$route.query.q ?? '')) return
      this.timer = setTimeout(() => this.search(term), DEBOUNCE_MS)
    },
  },
  beforeUnmount() {
    clearTimeout(this.timer)
  },
  methods: {
    search(term) {
      this.$router.replace({ query: term.trim() ? { q: term.trim() } : {} })
    },
    openDialog() {
      this.draft = this.term
      this.$refs.dialog.open()
      this.$nextTick(() => this.$refs.dialogInput.focus())
    },
    submitDialog() {
      this.term = this.draft.trim()
      this.search(this.term)
      this.$refs.dialog.close()
    },
  },
}
</script>

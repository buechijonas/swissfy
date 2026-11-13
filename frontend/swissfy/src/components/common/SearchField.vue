<template>
  <label class="input w-full mb-4 max-lg:hidden">
    <AppIcon name="search" class="text-app-muted" />
    <input
      v-model="term"
      type="search"
      class="grow"
      :placeholder="placeholder"
      autocomplete="off"
    />
  </label>
  <BaseDialog ref="dialog" title="Suchen">
    <form id="search-dialog-form" @submit.prevent="submitDialog">
      <label class="input w-full">
        <AppIcon name="search" class="text-app-muted" />
        <input
          v-model="draft"
          autofocus
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
</template>

<script>
import debounce from 'lodash-es/debounce'
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import { useAddButtonStore } from '@/stores/addButton.js'

const DEBOUNCE_MS = 300

export default {
  name: 'SearchField',
  components: { AppIcon, BaseButton, BaseDialog },
  props: {
    placeholder: { type: String, required: true },
  },
  data() {
    return {
      term: this.$route.query.q ?? '',
      draft: '',
    }
  },
  watch: {
    term(term) {
      if (term.trim() === (this.$route.query.q ?? '')) {
        this.debouncedSearch.cancel()
        return
      }
      this.debouncedSearch(term)
    },
  },
  beforeCreate() {
    this.owner = Symbol('SearchField')
  },
  created() {
    this.debouncedSearch = debounce(this.search, DEBOUNCE_MS)
    useAddButtonStore().show(this.owner, {
      label: 'Suchen',
      icon: 'search',
      loading: false,
      onClick: () => this.openDialog(),
    })
  },
  beforeUnmount() {
    this.debouncedSearch.cancel()
    useAddButtonStore().hide(this.owner)
  },
  methods: {
    search(term) {
      this.$router.replace({ query: term.trim() ? { q: term.trim() } : {} })
    },
    openDialog() {
      this.draft = this.term
      this.$refs.dialog.open()
    },
    submitDialog() {
      this.term = this.draft.trim()
      this.search(this.term)
      this.$refs.dialog.close()
    },
  },
}
</script>

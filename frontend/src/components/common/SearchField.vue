<template>
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
</template>

<script>
import AppIcon from '@/components/common/AppIcon.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import SearchButton from '@/components/common/SearchButton.vue'

const DEBOUNCE_MS = 300

export default {
  name: 'SearchField',
  components: { AppIcon, BaseButton, BaseDialog, SearchButton },
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

<template>
  <div>
    <BaseCard class="p-6 flex flex-col gap-4">
      <div
        class="flex flex-col items-center text-center gap-4 sm:flex-row sm:items-center sm:text-left sm:justify-between"
      >
        <div class="min-w-0">
          <p>{{ label }}</p>
          <p class="text-swissfy-muted text-sm mt-1">Wähle bis zu {{ max }}.</p>
        </div>
        <BaseButton
          class="shrink-0"
          size="sm"
          variant="primary"
          :disabled="disabled || items.length >= max"
          @click="openDialog"
        >
          <AppIcon name="plus" />
          Hinzufügen
        </BaseButton>
      </div>
      <ul v-if="items.length" class="grid grid-cols-3 gap-4">
        <li v-for="item in items" :key="item.id" class="flex flex-col gap-2 min-w-0">
          <FavoriteCover :item="item" :icon="icon" />
          <p class="text-sm truncate" :title="item.title">{{ item.title }}</p>
          <BaseButton
            size="sm"
            variant="error"
            outline
            :disabled="disabled"
            @click="
              $emit(
                'update',
                ids.filter((id) => id !== item.id),
              )
            "
          >
            <AppIcon name="trash" />
            Entfernen
          </BaseButton>
        </li>
      </ul>
    </BaseCard>

    <BaseDialog ref="dialog" :title="`${label} suchen`" box-class="max-w-2xl h-[80dvh]">
      <label class="input w-full shrink-0">
        <AppIcon name="search" class="text-swissfy-muted" />
        <input
          ref="input"
          v-model="query"
          type="search"
          class="grow"
          :placeholder="placeholder"
          autocomplete="off"
          enterkeyhint="search"
        />
      </label>
      <div class="mt-4 flex-1 min-h-0 overflow-y-auto">
        <p v-if="error" class="text-error text-sm text-center">{{ error }}</p>
        <div v-else-if="loading" class="grid grid-cols-3 sm:grid-cols-4 gap-4">
          <div v-for="n in 8" :key="n" class="skeleton aspect-2/3 w-full"></div>
        </div>
        <p v-else-if="query.trim() && !results.length" class="text-swissfy-muted text-center">
          Nichts gefunden.
        </p>
        <ul v-else class="grid grid-cols-3 sm:grid-cols-4 gap-4">
          <li v-for="item in results" :key="item.id" class="min-w-0">
            <button
              type="button"
              class="flex w-full flex-col gap-2 text-left rounded-box disabled:opacity-50"
              :disabled="ids.includes(item.id)"
              @click="select(item)"
            >
              <FavoriteCover :item="item" :icon="icon" />
              <span class="text-sm truncate w-full" :title="item.title">{{ item.title }}</span>
              <span v-if="item.year" class="text-xs text-swissfy-muted">{{ item.year }}</span>
            </button>
          </li>
        </ul>
      </div>
      <LibraryCredits class="mt-4 shrink-0" />
    </BaseDialog>
  </div>
</template>

<script>
import AppIcon from '@/components/common/AppIcon.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import FavoriteCover from '@/components/settings/FavoriteCover.vue'
import LibraryCredits from '@/components/settings/LibraryCredits.vue'
import profilesApi from '@/api/profiles.js'

const DEBOUNCE_MS = 300

export default {
  name: 'FavoritePicker',
  components: { AppIcon, BaseButton, BaseCard, BaseDialog, FavoriteCover, LibraryCredits },
  props: {
    kind: { type: String, required: true },
    label: { type: String, required: true },
    icon: { type: String, required: true },
    placeholder: { type: String, required: true },
    items: { type: Array, required: true },
    max: { type: Number, default: 3 },
    disabled: { type: Boolean, default: false },
  },
  emits: ['update'],
  data() {
    return {
      query: '',
      results: [],
      loading: false,
      error: null,
    }
  },
  computed: {
    ids() {
      return this.items.map((item) => item.id)
    },
  },
  watch: {
    query(query) {
      clearTimeout(this.timer)
      this.error = null
      if (!query.trim()) {
        this.results = []
        this.loading = false
        return
      }
      this.loading = true
      this.timer = setTimeout(() => this.search(query.trim()), DEBOUNCE_MS)
    },
  },
  beforeUnmount() {
    clearTimeout(this.timer)
  },
  methods: {
    openDialog() {
      this.query = ''
      this.$refs.dialog.open()
      this.$nextTick(() => this.$refs.input.focus())
    },
    async search(query) {
      try {
        const data = await profilesApi.searchLibrary(this.kind, query)
        if (query === this.query.trim()) this.results = data.results
      } catch (error) {
        if (query === this.query.trim()) this.error = error.detail ?? 'Suche fehlgeschlagen.'
      } finally {
        if (query === this.query.trim()) this.loading = false
      }
    },
    select(item) {
      this.$refs.dialog.close()
      this.$emit('update', [...this.ids, item.id])
    },
  },
}
</script>

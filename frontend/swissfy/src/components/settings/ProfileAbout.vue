<template>
  <h3 class="mt-10 mb-4 text-xl">{{ $t('about.title') }}</h3>
  <BaseCard class="flex flex-col gap-2 p-6">
    <label for="biography">{{ $t('about.biography') }}</label>
    <textarea
      id="biography"
      v-model="biography"
      class="textarea h-28 w-full resize-none"
      :maxlength="maxLength"
      :disabled="!about || action.busy"
      :placeholder="$t('about.placeholder')"
    ></textarea>
    <div class="flex items-center justify-between gap-4">
      <span class="text-xs text-app-muted">{{ biography.length }}/{{ maxLength }}</span>
      <BaseButton
        size="sm"
        variant="primary"
        :disabled="!about || action.busy || biography === about.biography"
        @click="save({ biography })"
      >
        <AppIcon name="disk" />
        {{ $t('common.save') }}
      </BaseButton>
    </div>
  </BaseCard>
  <template v-if="about">
    <FavoritePicker
      v-for="favorite in favoriteKinds"
      :key="favorite.kind"
      class="mt-4"
      :kind="favorite.kind"
      :label="favorite.label"
      :icon="favorite.icon"
      :placeholder="favorite.placeholder"
      :items="about[favorite.field]"
      :disabled="action.busy"
      @update="save({ [favorite.field]: $event })"
    />
  </template>
  <div v-else-if="!action.error" class="mt-4 h-24 w-full skeleton rounded-box"></div>
  <ErrorText :message="action.error" class="mt-4 text-center" />
</template>

<script>
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import BaseCard from '@core/components/BaseCard.vue'
import ErrorText from '@core/components/ErrorText.vue'
import { useAsyncAction } from '@core/composables/asyncAction.js'
import profilesApi from '@/api/profiles.js'
import FavoritePicker from '@/components/settings/FavoritePicker.vue'
import { favoriteKinds } from '@/data/favorites.js'
import { t } from '@/i18n.js'

export default {
  name: 'ProfileAbout',
  components: { AppIcon, BaseButton, BaseCard, FavoritePicker, ErrorText },
  data() {
    return {
      action: useAsyncAction(),
      maxLength: 500,
      about: null,
      biography: '',
    }
  },
  computed: {
    favoriteKinds,
  },
  mounted() {
    this.load()
  },
  methods: {
    async load() {
      try {
        this.about = await profilesApi.about()
        this.biography = this.about.biography
      } catch {
        this.action.error = t('about.loadFailed')
      }
    },
    async save(changes) {
      const about = await this.action.run(
        () => profilesApi.updateAbout(changes),
        t('common.saveFailed'),
      )
      if (about) this.about = about
    },
  },
}
</script>

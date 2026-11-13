<template>
  <h3 class="text-xl mt-10 mb-4">Info</h3>
  <BaseCard class="p-6 flex flex-col gap-2">
    <label for="biography">Biografie</label>
    <textarea
      id="biography"
      v-model="biography"
      class="textarea w-full h-28 resize-none"
      :maxlength="maxLength"
      :disabled="!about || busy"
      placeholder="Erzähl etwas über dich"
    ></textarea>
    <div class="flex items-center justify-between gap-4">
      <span class="text-xs text-app-muted">{{ biography.length }}/{{ maxLength }}</span>
      <BaseButton
        size="sm"
        variant="primary"
        :disabled="!about || busy || biography === about.biography"
        @click="save({ biography })"
      >
        <AppIcon name="disk" />
        Speichern
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
      :disabled="busy"
      @update="save({ [favorite.field]: $event })"
    />
  </template>
  <div v-else-if="!error" class="skeleton mt-4 h-24 w-full rounded-box"></div>
  <ErrorText :message="error" class="mt-4 text-center" />
</template>

<script>
import ErrorText from '@core/components/ErrorText.vue'
import asyncActionMixin from '@core/mixins/asyncActionMixin.js'
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import BaseCard from '@core/components/BaseCard.vue'
import FavoritePicker from '@/components/settings/FavoritePicker.vue'
import { favoriteKinds } from '@/data/favorites.js'
import profilesApi from '@/api/profiles.js'

export default {
  name: 'ProfileAbout',
  mixins: [asyncActionMixin],
  components: { AppIcon, BaseButton, BaseCard, FavoritePicker, ErrorText },
  data() {
    return {
      favoriteKinds,
      maxLength: 500,
      about: null,
      biography: '',
    }
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
        this.error = 'Infos konnten nicht geladen werden.'
      }
    },
    async save(changes) {
      const about = await this.runAction(
        () => profilesApi.updateAbout(changes),
        'Speichern fehlgeschlagen.',
      )
      if (about) this.about = about
    },
  },
}
</script>

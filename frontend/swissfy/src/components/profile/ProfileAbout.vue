<template>
  <BaseCard class="flex flex-col gap-6 border-t-0 p-6">
    <p v-if="profile.biography" class="break-words whitespace-pre-line">
      {{ profile.biography }}
    </p>
    <dl v-if="profile.birthdate" class="flex justify-between gap-4">
      <dt class="text-app-muted">{{ $t('profile.birthdate') }}</dt>
      <dd>{{ formatDate(profile.birthdate) }}</dd>
    </dl>
    <section v-for="favorite in favorites" :key="favorite.kind">
      <h4 class="mb-2 text-app-muted">{{ favorite.label }}</h4>
      <ul class="grid grid-cols-3 gap-4">
        <li v-for="item in profile[favorite.field]" :key="item.id" class="min-w-0">
          <FavoriteCover :item="item" :icon="favorite.icon" />
          <p class="mt-2 truncate text-sm" :title="item.title">{{ item.title }}</p>
          <p v-if="item.year" class="text-xs text-app-muted">{{ item.year }}</p>
        </li>
      </ul>
    </section>
    <LibraryCredits v-if="favorites.length" />
    <p v-if="!profile.biography && !profile.birthdate && !favorites.length" class="text-app-muted">
      {{ $t('profile.noDetails') }}
    </p>
  </BaseCard>
</template>

<script>
import BaseCard from '@core/components/BaseCard.vue'
import FavoriteCover from '@/components/settings/FavoriteCover.vue'
import LibraryCredits from '@/components/settings/LibraryCredits.vue'
import { favoriteKinds } from '@/data/favorites.js'
import { formatDate } from '@/lib/time.js'

export default {
  name: 'ProfileAbout',
  components: { BaseCard, FavoriteCover, LibraryCredits },
  props: {
    profile: { type: Object, required: true },
  },
  computed: {
    favorites() {
      return favoriteKinds().filter((favorite) => this.profile[favorite.field]?.length)
    },
  },
  methods: {
    formatDate,
  },
}
</script>

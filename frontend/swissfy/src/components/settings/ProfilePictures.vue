<template>
  <h3 class="text-xl my-4">Profilbilder</h3>
  <div class="flex flex-col gap-4">
    <BaseCard v-for="card in cards" :key="card.kind" class="p-6 flex flex-col gap-4">
      <div class="flex flex-col items-center text-center gap-4 sm:flex-row sm:text-left">
        <img
          v-if="settings?.[`${card.kind}_picture`]"
          class="size-20 shrink-0 rounded-full object-cover"
          :src="settings[`${card.kind}_picture`]"
          alt=""
        />
        <img v-else-if="card.fallback" class="size-20 shrink-0" :src="card.fallback" alt="" />
        <div
          v-else
          class="flex size-20 shrink-0 items-center justify-center rounded-full bg-base-200 text-app-muted"
        >
          <AppIcon name="picture" class="size-8!" />
        </div>
        <div class="min-w-0 flex-1">
          <p>{{ card.label }}</p>
          <p class="text-app-muted text-sm mt-1">{{ card.hint }}</p>
        </div>
        <div v-if="settings" class="flex flex-wrap justify-center gap-2 shrink-0">
          <BaseButton
            size="sm"
            variant="primary"
            accept="image/*"
            :disabled="busy"
            @files="(files) => upload(card.kind, files)"
          >
            <AppIcon name="picture" />
            Hochladen
          </BaseButton>
          <BaseButton
            v-if="settings[`${card.kind}_picture`]"
            size="sm"
            variant="error"
            outline
            :disabled="busy"
            @click="remove(card.kind)"
          >
            <AppIcon name="trash" />
            Entfernen
          </BaseButton>
        </div>
        <div v-else-if="!error" class="skeleton h-8 w-28"></div>
      </div>
      <div v-if="card.kind === 'private' && settings">
        <VisibilityPicker
          :visibility="settings.private_picture_visibility"
          :groups="settings.private_picture_groups"
          :allow-public="false"
          @update:visibility="saveAudience($event, settings.private_picture_groups)"
          @update:groups="saveAudience(settings.private_picture_visibility, $event)"
        />
      </div>
    </BaseCard>
  </div>
  <ErrorText :message="error" class="mt-4 text-center" />
</template>

<script>
import ErrorText from '@core/components/ErrorText.vue'
import asyncActionMixin from '@core/mixins/asyncActionMixin.js'
import { mapStores } from 'pinia'
import head from 'lodash-es/head'
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import BaseCard from '@core/components/BaseCard.vue'
import VisibilityPicker from '@/components/posts/VisibilityPicker.vue'
import { avatars } from '@/assets/images.js'
import profilesApi from '@/api/profiles.js'
import { compressImage } from '@/lib/image.js'
import { useAuthStore } from '@/stores/auth.js'
import { useGroupsStore } from '@/stores/posts.js'

export default {
  name: 'ProfilePictures',
  mixins: [asyncActionMixin],
  components: { AppIcon, BaseButton, BaseCard, VisibilityPicker, ErrorText },
  data() {
    return {
      settings: null,
    }
  },
  computed: {
    ...mapStores(useAuthStore),
    cards() {
      return [
        {
          kind: 'public',
          label: 'Öffentliches Profilbild',
          hint: 'Sehen alle. Ohne eigenes Bild wird dein govex Profilbild verwendet.',
          fallback: avatars[this.authStore.user?.avatar],
        },
        {
          kind: 'private',
          label: 'Privates Profilbild',
          hint: 'Sehen nur die ausgewählten Personen, alle anderen sehen dein öffentliches Bild.',
        },
      ]
    },
  },
  mounted() {
    this.load()
    useGroupsStore()
      .load()
      .catch(() => {})
  },
  methods: {
    async load() {
      try {
        this.settings = await profilesApi.pictures()
      } catch {
        this.error = 'Profilbilder konnten nicht geladen werden.'
      }
    },
    async request(action) {
      const settings = await this.runAction(action, 'Speichern fehlgeschlagen.')
      if (!settings) return
      this.settings = settings
      this.authStore.user = {
        ...this.authStore.user,
        picture: settings.private_picture ?? settings.public_picture,
      }
    },
    async upload(kind, files) {
      const file = head(files)
      if (!file) return
      const body = new FormData()
      body.append(`${kind}_picture`, await compressImage(file), file.name)
      await this.request(() => profilesApi.updatePictures(body))
    },
    remove(kind) {
      return this.request(() => profilesApi.removePicture(kind))
    },
    saveAudience(visibility, groups) {
      this.settings = {
        ...this.settings,
        private_picture_visibility: visibility,
        private_picture_groups: groups,
      }
      if (visibility === 'groups' && !groups.length) return
      return this.request(() =>
        profilesApi.updatePictures({
          private_picture_visibility: visibility,
          private_picture_groups: groups,
        }),
      )
    },
  },
}
</script>

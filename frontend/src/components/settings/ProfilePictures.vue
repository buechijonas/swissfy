<template>
  <h3 class="text-xl my-4">Profilbilder</h3>
  <BaseCard
    v-for="(card, index) in cards"
    :key="card.kind"
    class="p-6 flex flex-col gap-4"
    :class="{ 'mt-4': index }"
  >
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
        class="flex size-20 shrink-0 items-center justify-center rounded-full bg-base-200 text-swissfy-muted"
      >
        <AppIcon name="picture" class="size-8!" />
      </div>
      <div class="min-w-0 flex-1">
        <p>{{ card.label }}</p>
        <p class="text-swissfy-muted text-sm">{{ card.hint }}</p>
      </div>
      <div v-if="settings" class="flex flex-wrap justify-center gap-2 shrink-0">
        <BaseButton size="sm" variant="primary" :disabled="busy" @click="choose(card.kind)">
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
  <input ref="file" type="file" accept="image/*" class="sr-only" @change="upload" />
  <p v-if="error" class="text-error text-sm mt-4 text-center">{{ error }}</p>
</template>

<script>
import AppIcon from '@/components/common/AppIcon.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import VisibilityPicker from '@/components/posts/VisibilityPicker.vue'
import { avatars } from '@/assets/images.js'
import { apiFetch, extractErrorMessage } from '@/lib/api.js'
import { compressImage } from '@/lib/image.js'
import { useAuthStore } from '@/stores/auth.js'
import { useGroupsStore } from '@/stores/posts.js'

const URL = '/api/social/profiles/me/pictures/'

export default {
  name: 'ProfilePictures',
  components: { AppIcon, BaseButton, BaseCard, VisibilityPicker },
  data() {
    return {
      settings: null,
      kind: null,
      busy: false,
      error: null,
    }
  },
  computed: {
    authStore() {
      return useAuthStore()
    },
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
      const response = await apiFetch(URL).catch(() => null)
      if (response?.ok) {
        this.settings = await response.json()
      } else {
        this.error = 'Profilbilder konnten nicht geladen werden.'
      }
    },
    async request(url, options) {
      this.busy = true
      this.error = null
      try {
        const response = await apiFetch(url, options)
        const data = await response.json().catch(() => null)
        if (!response.ok) {
          this.error = extractErrorMessage(data, 'Speichern fehlgeschlagen.')
          return
        }
        this.settings = data
        this.authStore.user = {
          ...this.authStore.user,
          picture: data.private_picture ?? data.public_picture,
        }
      } catch {
        this.error = 'Speichern fehlgeschlagen.'
      } finally {
        this.busy = false
      }
    },
    choose(kind) {
      this.kind = kind
      this.$refs.file.click()
    },
    async upload(event) {
      const [file] = event.target.files
      event.target.value = ''
      if (!file) return
      const body = new FormData()
      body.append(`${this.kind}_picture`, await compressImage(file), file.name)
      await this.request(URL, { method: 'PATCH', body })
    },
    remove(kind) {
      return this.request(`${URL}${kind}/`, { method: 'DELETE' })
    },
    saveAudience(visibility, groups) {
      this.settings = {
        ...this.settings,
        private_picture_visibility: visibility,
        private_picture_groups: groups,
      }
      if (visibility === 'groups' && !groups.length) return
      return this.request(URL, {
        method: 'PATCH',
        body: JSON.stringify({
          private_picture_visibility: visibility,
          private_picture_groups: groups,
        }),
      })
    },
  },
}
</script>

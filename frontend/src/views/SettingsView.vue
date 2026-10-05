<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div
    class="flex flex-col pb-8 px-6 max-h-[calc(100dvh-101px)] overflow-y-auto lg:max-h-none lg:overflow-y-visible lg:flex-1"
  >
    <div class="mx-auto w-full max-w-150">
      <h2 class="text-xl font-light my-4">Einstellungen</h2>

      <div v-if="!authStore.ready" class="mb-10">
        <div class="skeleton my-5 h-5 w-24"></div>
        <div class="skeleton h-24 w-full rounded-box"></div>
      </div>
      <div v-else-if="authStore.isAuthenticated" class="mb-10">
        <h3 class="text-xl my-4">Konto</h3>
        <BaseCard class="p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <p class="text-swissfy-muted min-w-0">
            Profil, Profilbild, Passwort und Sicherheit verwaltest du im govex Account Center.
          </p>
          <BaseButton class="shrink-0" @click="authStore.openGovexAccount()">
            <AppIcon name="share-square" />
            Zum Account Center
          </BaseButton>
        </BaseCard>
      </div>

      <div class="mb-10">
        <h3 class="text-xl my-4">Darstellung</h3>
        <BaseCard
          class="p-6 flex flex-col items-center text-center gap-4"
          :class="{ 'sm:flex-row sm:items-center sm:text-left sm:justify-between': !dyslexiaFont }"
        >
          <p class="text-swissfy-muted min-w-0">Erscheinungsbild der Oberfläche.</p>
          <div class="flex flex-wrap justify-center gap-2">
            <BaseButton
              v-for="option in themeOptions"
              :key="option.value"
              type="button"
              size="sm"
              :variant="themeMode === option.value ? 'primary' : 'neutral'"
              @click="themeMode = option.value"
            >
              <AppIcon :name="option.icon" />
              {{ option.label }}
            </BaseButton>
          </div>
        </BaseCard>
      </div>

      <div class="mb-10">
        <h3 class="text-xl my-4">Barrierefreiheit</h3>
        <BaseCard
          class="p-6 flex flex-col items-center text-center gap-4 mb-4 sm:flex-row sm:items-center sm:text-left sm:justify-between"
        >
          <p class="text-swissfy-muted min-w-0">Legasthenie</p>
          <div class="flex flex-wrap justify-center gap-2">
            <BaseButton
              v-for="option in dyslexiaOptions"
              :key="option.value"
              type="button"
              size="sm"
              :variant="dyslexiaFont === option.value ? 'primary' : 'neutral'"
              @click="dyslexiaFont = option.value"
            >
              {{ option.label }}
            </BaseButton>
          </div>
        </BaseCard>
        <BaseCard
          class="p-6 flex flex-col items-center text-center gap-4 sm:flex-row sm:items-center sm:text-left sm:justify-between"
        >
          <p class="text-swissfy-muted min-w-0">Kontrastmodus</p>
          <div class="flex flex-wrap justify-center gap-2">
            <BaseButton
              v-for="option in contrastOptions"
              :key="option.value"
              type="button"
              size="sm"
              :variant="contrastMode === option.value ? 'primary' : 'neutral'"
              @click="contrastMode = option.value"
            >
              {{ option.label }}
            </BaseButton>
          </div>
        </BaseCard>
      </div>
    </div>
  </div>
  <BaseFooter />
</template>

<script>
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import AppIcon from '@/components/common/AppIcon.vue'
import { useAuthStore } from '@/stores/auth.js'
import { themeMode } from '@/lib/theme.js'
import { dyslexiaFont } from '@/lib/dyslexia.js'
import { contrastMode } from '@/lib/contrast.js'

export default {
  name: 'SettingsView',
  components: { BaseBreadcrumbs, BaseCard, BaseFooter, BaseButton, AppIcon },
  data() {
    return {
      breadcrumbs: [{ label: 'Einstellungen', to: '/' }],
      themeOptions: [
        { value: 'auto', icon: 'laptop', label: 'Auto' },
        { value: 'light', icon: 'brightness', label: 'Hell' },
        { value: 'dark', icon: 'moon-stars', label: 'Dunkel' },
      ],
      dyslexiaOptions: [
        { value: true, label: 'An' },
        { value: false, label: 'Aus' },
      ],
      contrastOptions: [
        { value: true, label: 'An' },
        { value: false, label: 'Aus' },
      ],
    }
  },
  computed: {
    authStore() {
      return useAuthStore()
    },
    themeMode: {
      get() {
        return themeMode.value
      },
      set(value) {
        themeMode.value = value
      },
    },
    dyslexiaFont: {
      get() {
        return dyslexiaFont.value
      },
      set(value) {
        dyslexiaFont.value = value
      },
    },
    contrastMode: {
      get() {
        return contrastMode.value
      },
      set(value) {
        contrastMode.value = value
      },
    },
  },
}
</script>

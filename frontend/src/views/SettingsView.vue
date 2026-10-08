<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div
    class="flex flex-col pb-8 px-6 max-h-[calc(100dvh-48px)] overflow-y-auto lg:max-h-none lg:overflow-y-visible lg:flex-1"
  >
    <div class="mx-auto w-full max-w-150">
      <h2 class="text-xl font-light my-4">Einstellungen</h2>

      <div v-if="!authStore.ready" class="mb-10">
        <div class="skeleton mb-2 h-10 w-full"></div>
        <div class="skeleton my-5 h-5 w-24"></div>
        <div class="skeleton h-24 w-full rounded-box"></div>
      </div>

      <template v-else>
        <div role="tablist" class="tabs mb-2">
          <RouterLink
            v-for="tab in tabs"
            :key="tab.key"
            role="tab"
            class="tab border-b-2"
            :class="activeTab === tab.key ? 'tab-active border-current' : 'border-transparent'"
            :aria-selected="activeTab === tab.key"
            :to="{ query: { tab: tab.key } }"
            replace
          >
            {{ tab.label }}
          </RouterLink>
        </div>

        <template v-if="activeTab === 'general'">
          <div class="mb-10">
            <h3 class="text-xl my-4">Konto</h3>
            <BaseCard
              v-if="authStore.isAuthenticated"
              class="p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
            >
              <p class="text-swissfy-muted min-w-0">
                Profil, Profilbild, Passwort und Sicherheit verwaltest du im govex Account Center.
              </p>
              <BaseButton class="shrink-0" @click="authStore.openGovexAccount()">
                <AppIcon name="share-square" />
                Zum Account Center
              </BaseButton>
            </BaseCard>
            <BaseCard
              v-else
              class="p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
            >
              <p class="text-swissfy-muted min-w-0">Melde dich mit deinem govex Konto an.</p>
              <BaseButton class="shrink-0" @click="authStore.startGovexLogin()">
                Anmelden
              </BaseButton>
            </BaseCard>
          </div>

          <div class="mb-10 max-lg:hidden">
            <h3 class="text-xl my-4">Rechtliches</h3>
            <div class="flex flex-col gap-4">
              <RouterLink v-for="link in footerLinks" :key="link.to" :to="link.to">
                <BaseCard class="p-6 flex items-center gap-4 hover:bg-swissfy-highlight">
                  <AppIcon :name="link.icon" :alt="link.label" class="size-5!" />
                  <span>{{ link.label }}</span>
                </BaseCard>
              </RouterLink>
            </div>
          </div>
        </template>

        <div v-else-if="activeTab === 'profile'" class="mb-10">
          <h3 class="text-xl my-4">Datenschutz</h3>
          <BaseCard
            class="p-6 flex flex-col items-center text-center gap-4 sm:flex-row sm:items-center sm:text-left sm:justify-between"
          >
            <div class="min-w-0">
              <p>Profil sichtbar für</p>
              <p class="text-swissfy-muted text-sm">Gilt auch für deinen Vor- und Nachnamen.</p>
            </div>
            <div v-if="profileVisibility" class="flex flex-wrap justify-center gap-2">
              <BaseButton
                v-for="option in visibilityOptions"
                :key="option.value"
                type="button"
                size="sm"
                :variant="profileVisibility === option.value ? 'primary' : 'neutral'"
                :disabled="savingPrivacy"
                @click="saveProfileVisibility(option.value)"
              >
                {{ option.label }}
              </BaseButton>
            </div>
            <div v-else-if="!privacyError" class="skeleton h-8 w-56"></div>
          </BaseCard>
          <p v-if="privacyError" class="text-error text-sm mt-4 text-center">{{ privacyError }}</p>
        </div>

        <template v-else>
          <div class="mb-10">
            <h3 class="text-xl my-4">Darstellung</h3>
            <BaseCard
              class="p-6 flex flex-col items-center text-center gap-4"
              :class="{
                'sm:flex-row sm:items-center sm:text-left sm:justify-between': !dyslexiaFont,
              }"
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
        </template>
      </template>
    </div>
  </div>
  <BaseFooter />
</template>

<script>
import { RouterLink } from 'vue-router'
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import AppIcon from '@/components/common/AppIcon.vue'
import { useAuthStore } from '@/stores/auth.js'
import { themeMode } from '@/lib/theme.js'
import { dyslexiaFont } from '@/lib/dyslexia.js'
import { contrastMode } from '@/lib/contrast.js'
import { apiFetch, extractErrorMessage } from '@/lib/api.js'
import { footerLinks } from '@/data/footer.js'

const PRIVACY_URL = '/api/social/profiles/me/privacy/'

export default {
  name: 'SettingsView',
  components: { RouterLink, BaseBreadcrumbs, BaseCard, BaseFooter, BaseButton, AppIcon },
  data() {
    return {
      breadcrumbs: [{ label: 'Einstellungen', to: '/' }],
      footerLinks,
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
      visibilityOptions: [
        { value: 'public', label: 'Öffentlich' },
        { value: 'followers', label: 'Follower' },
        { value: 'friends', label: 'Freunde' },
      ],
      profileVisibility: null,
      savingPrivacy: false,
      privacyError: null,
    }
  },
  computed: {
    authStore() {
      return useAuthStore()
    },
    tabs() {
      return [
        { key: 'general', label: 'Allgemein' },
        ...(this.authStore.isAuthenticated ? [{ key: 'profile', label: 'Profil' }] : []),
        { key: 'display', label: 'Darstellung' },
      ]
    },
    activeTab() {
      const tab = this.$route.query.tab
      return this.tabs.some((t) => t.key === tab) ? tab : this.tabs[0].key
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
  watch: {
    activeTab: {
      immediate: true,
      handler(tab) {
        if (tab === 'profile' && !this.profileVisibility) this.loadPrivacy()
      },
    },
  },
  methods: {
    async loadPrivacy() {
      this.privacyError = null
      const response = await apiFetch(PRIVACY_URL)
      if (response.ok) {
        this.profileVisibility = (await response.json()).profile_visibility
      } else {
        this.privacyError = 'Einstellungen konnten nicht geladen werden.'
      }
    },
    async saveProfileVisibility(value) {
      const previous = this.profileVisibility
      this.profileVisibility = value
      this.savingPrivacy = true
      this.privacyError = null
      try {
        const response = await apiFetch(PRIVACY_URL, {
          method: 'PATCH',
          body: JSON.stringify({ profile_visibility: value }),
        })
        if (!response.ok) {
          const data = await response.json().catch(() => null)
          this.privacyError = extractErrorMessage(data, 'Speichern fehlgeschlagen.')
          this.profileVisibility = previous
        }
      } finally {
        this.savingPrivacy = false
      }
    },
  },
}
</script>

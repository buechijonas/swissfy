<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div
    class="flex flex-col pb-8 px-6 max-h-[calc(100dvh-96px)] overflow-y-auto lg:max-h-none lg:overflow-y-visible lg:flex-1"
  >
    <div class="mx-auto w-full max-w-150 sm:pt-4">
      <div v-if="!authStore.ready" class="mb-10">
        <div class="skeleton mb-2 h-10 w-full"></div>
        <div class="skeleton my-5 h-5 w-24"></div>
        <div class="skeleton h-24 w-full rounded-box"></div>
      </div>

      <template v-else>
        <BaseTabs :tabs="tabs" :active="activeTab" />

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

          <div class="mb-10">
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
            <div v-if="privacy" class="flex flex-wrap justify-center gap-2">
              <BaseButton
                v-for="option in visibilityOptions"
                :key="option.value"
                type="button"
                size="sm"
                :variant="privacy.profile_visibility === option.value ? 'primary' : 'neutral'"
                :disabled="savingPrivacy"
                @click="savePrivacy('profile_visibility', option.value)"
              >
                {{ option.label }}
              </BaseButton>
            </div>
            <div v-else-if="!privacyError" class="skeleton h-8 w-56"></div>
          </BaseCard>
          <BaseCard
            v-for="toggle in privacyToggles"
            :key="toggle.field"
            class="p-6 mt-4 flex flex-col items-center text-center gap-4 sm:flex-row sm:items-center sm:text-left sm:justify-between"
          >
            <div class="min-w-0">
              <p>{{ toggle.label }}</p>
              <p class="text-swissfy-muted text-sm">{{ toggle.hint }}</p>
            </div>
            <div v-if="privacy" class="flex flex-wrap justify-center gap-2 shrink-0">
              <BaseButton
                v-for="option in onOffOptions"
                :key="option.label"
                type="button"
                size="sm"
                :variant="privacy[toggle.field] === option.value ? 'primary' : 'neutral'"
                :disabled="savingPrivacy"
                @click="savePrivacy(toggle.field, option.value)"
              >
                {{ option.label }}
              </BaseButton>
            </div>
            <div v-else-if="!privacyError" class="skeleton h-8 w-28"></div>
          </BaseCard>
          <p v-if="privacyError" class="text-error text-sm mt-4 text-center">{{ privacyError }}</p>

          <BaseCard class="p-6 mt-4 flex flex-col gap-4">
            <div
              class="flex flex-col items-center text-center gap-4 sm:flex-row sm:items-center sm:text-left sm:justify-between"
            >
              <div class="min-w-0">
                <p>Chat-Verschlüsselung</p>
                <p v-if="chatProtection" class="text-swissfy-muted text-sm">
                  {{ chatProtectionHints[chatProtection] }}
                </p>
              </div>
              <div v-if="chatProtection" class="flex flex-wrap justify-center gap-2 shrink-0">
                <BaseButton
                  v-for="option in chatProtectionOptions"
                  :key="option.value"
                  type="button"
                  size="sm"
                  :variant="chatProtection === option.value ? 'primary' : 'neutral'"
                  :disabled="savingChat"
                  @click="selectChatProtection(option.value)"
                >
                  {{ option.label }}
                </BaseButton>
              </div>
              <div v-else-if="!chatError" class="skeleton h-8 w-56"></div>
            </div>
            <form v-if="pinSetup" class="flex flex-col gap-2" @submit.prevent="savePin">
              <input
                v-model="newPin"
                type="password"
                autocomplete="new-password"
                class="input w-full"
                placeholder="Neue Chat-PIN (mindestens 6 Zeichen)"
              />
              <input
                v-model="newPinRepeat"
                type="password"
                autocomplete="new-password"
                class="input w-full"
                placeholder="Chat-PIN wiederholen"
              />
              <p class="text-swissfy-muted text-sm">
                Ohne PIN kann niemand deine Chats wiederherstellen, auch wir nicht.
              </p>
              <div class="flex justify-end gap-2">
                <BaseButton size="sm" :disabled="savingChat" @click="pinSetup = false">
                  Abbrechen
                </BaseButton>
                <BaseButton
                  type="submit"
                  size="sm"
                  variant="primary"
                  :disabled="!pinValid || savingChat"
                >
                  PIN festlegen
                </BaseButton>
              </div>
            </form>
            <p v-if="chatError" class="text-error text-sm text-center">{{ chatError }}</p>
          </BaseCard>
        </div>

        <div v-else-if="activeTab === 'groups'" class="mb-10">
          <h3 class="text-xl my-4">Gruppen</h3>
          <GroupManager />
        </div>

        <div v-else-if="activeTab === 'wellbeing'" class="mb-10">
          <h3 class="text-xl my-4">Suchtprävention</h3>
          <p class="text-swissfy-muted text-sm mb-4">
            Swissfy verzichtet standardmässig auf Funktionen, die dich länger am Bildschirm halten
            sollen. Du kannst sie hier bewusst einschalten. Gilt für dieses Gerät.
          </p>
          <BaseCard
            v-for="(toggle, index) in wellbeingToggles"
            :key="toggle.label"
            class="p-6 flex flex-col items-center text-center gap-4 sm:flex-row sm:items-center sm:text-left sm:justify-between"
            :class="{ 'mt-4': index }"
          >
            <div class="min-w-0">
              <p>{{ toggle.label }}</p>
              <p class="text-swissfy-muted text-sm">{{ toggle.hint }}</p>
            </div>
            <div class="flex flex-wrap justify-center gap-2 shrink-0">
              <BaseButton
                v-for="option in onOffOptions"
                :key="option.label"
                type="button"
                size="sm"
                :variant="toggle.setting.value === option.value ? 'primary' : 'neutral'"
                @click="toggle.setting.value = option.value"
              >
                {{ option.label }}
              </BaseButton>
            </div>
          </BaseCard>
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
import { markRaw } from 'vue'
import { RouterLink } from 'vue-router'
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseTabs from '@/components/common/BaseTabs.vue'
import AppIcon from '@/components/common/AppIcon.vue'
import GroupManager from '@/components/posts/GroupManager.vue'
import { useAuthStore } from '@/stores/auth.js'
import { themeMode } from '@/lib/theme.js'
import { dyslexiaFont } from '@/lib/dyslexia.js'
import { contrastMode } from '@/lib/contrast.js'
import { videoAutoplay, videoLoop } from '@/lib/wellbeing.js'
import { apiFetch, extractErrorMessage } from '@/lib/api.js'
import { footerLinks } from '@/data/footer.js'
import { fetchProtection, setProtection } from '@/lib/chatKeys.js'

const PRIVACY_URL = '/api/social/profiles/me/privacy/'

export default {
  name: 'SettingsView',
  components: {
    RouterLink,
    BaseBreadcrumbs,
    BaseCard,
    BaseFooter,
    BaseButton,
    BaseTabs,
    AppIcon,
    GroupManager,
  },
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
      chatProtectionOptions: [
        { value: 'standard', label: 'Standard' },
        { value: 'device', label: 'Nur auf diesem Gerät' },
        { value: 'pin', label: 'Chat-PIN' },
      ],
      chatProtectionHints: {
        standard: 'Verschlüsselt gespeichert. Zugang auf jedem Gerät mit deinem Login.',
        device:
          'Ende-zu-Ende verschlüsselt. Nur dieses Gerät kann deine Chats lesen, neue Geräte sehen nur neue Nachrichten.',
        pin: 'Ende-zu-Ende verschlüsselt. Auf neuen Geräten entsperrst du deine Chats mit deiner PIN.',
      },
      chatProtection: null,
      savingChat: false,
      chatError: null,
      pinSetup: false,
      newPin: '',
      newPinRepeat: '',
      visibilityOptions: [
        { value: 'public', label: 'Öffentlich' },
        { value: 'followers', label: 'Follower' },
        { value: 'friends', label: 'Freunde' },
      ],
      privacy: null,
      privacyToggles: [
        {
          field: 'read_receipts',
          label: 'Lesebestätigungen',
          hint: 'Wenn aus, sehen andere nicht, ob du ihre Nachrichten gelesen hast, und du siehst es bei ihnen auch nicht.',
        },
        {
          field: 'chat_requests',
          label: 'Chat-Anfragen',
          hint: 'Wenn aus, kann dir niemand eine neue Chat-Anfrage senden. Bestehende Chats bleiben.',
        },
        {
          field: 'show_birthdate',
          label: 'Geburtsdatum',
          hint: 'Wenn an, sehen alle, die dein Profil sehen dürfen, dein Geburtsdatum unter «Über mich».',
        },
      ],
      onOffOptions: [
        { value: true, label: 'An' },
        { value: false, label: 'Aus' },
      ],
      savingPrivacy: false,
      privacyError: null,
      wellbeingToggles: markRaw([
        {
          setting: videoAutoplay,
          label: 'Autoplay',
          hint: 'Wenn an, starten Videos von selbst und ohne Ton, sobald du zu ihnen scrollst.',
        },
        {
          setting: videoLoop,
          label: 'Wiederholen',
          hint: 'Wenn an, beginnen Videos am Ende automatisch von vorne.',
        },
      ]),
    }
  },
  computed: {
    authStore() {
      return useAuthStore()
    },
    tabs() {
      return [
        { key: 'general', label: 'Allgemein' },
        ...(this.authStore.isAuthenticated
          ? [
              { key: 'profile', label: 'Profil' },
              { key: 'groups', label: 'Gruppen' },
            ]
          : []),
        { key: 'display', label: 'Darstellung' },
        { key: 'wellbeing', label: 'Wohlbefinden' },
      ]
    },
    pinValid() {
      return this.newPin.length >= 6 && this.newPin === this.newPinRepeat
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
        if (tab !== 'profile') return
        if (!this.privacy) this.loadPrivacy()
        if (!this.chatProtection) this.loadChatProtection()
      },
    },
  },
  methods: {
    async loadChatProtection() {
      this.chatError = null
      try {
        this.chatProtection = (await fetchProtection()).mode
      } catch (error) {
        this.chatError = error.message
      }
    },
    selectChatProtection(mode) {
      this.chatError = null
      if (mode === 'pin') {
        this.pinSetup = true
      } else if (mode !== this.chatProtection) {
        this.pinSetup = false
        this.saveChatProtection(mode)
      }
    },
    savePin() {
      return this.saveChatProtection('pin', this.newPin)
    },
    async saveChatProtection(mode, pin) {
      this.savingChat = true
      this.chatError = null
      try {
        this.chatProtection = (await setProtection(this.authStore.user.id, mode, pin)).mode
        this.pinSetup = false
        this.newPin = ''
        this.newPinRepeat = ''
      } catch (error) {
        this.chatError = error.message
      } finally {
        this.savingChat = false
      }
    },
    async loadPrivacy() {
      this.privacyError = null
      const response = await apiFetch(PRIVACY_URL)
      if (response.ok) {
        this.privacy = await response.json()
      } else {
        this.privacyError = 'Einstellungen konnten nicht geladen werden.'
      }
    },
    async savePrivacy(field, value) {
      const previous = this.privacy[field]
      this.privacy[field] = value
      this.savingPrivacy = true
      this.privacyError = null
      try {
        const response = await apiFetch(PRIVACY_URL, {
          method: 'PATCH',
          body: JSON.stringify({ [field]: value }),
        })
        if (!response.ok) {
          const data = await response.json().catch(() => null)
          this.privacyError = extractErrorMessage(data, 'Speichern fehlgeschlagen.')
          this.privacy[field] = previous
        }
      } finally {
        this.savingPrivacy = false
      }
    },
  },
}
</script>

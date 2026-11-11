<template>
  <div class="mb-10">
    <h3 class="text-xl my-4">Datenschutz</h3>
    <SettingCard
      title="Profil sichtbar für"
      hint="Gilt auch für deinen Vor- und Nachnamen sowie deine Feeds und Seeds. Deine Profilbilder sind davon nicht betroffen, ihre Sichtbarkeit legst du unter «Profil» fest. Ist dein Profil privater eingestellt als ein Post, gilt für diesen Post die strengere Einstellung deines Profils."
    >
      <BaseSwitcher
        v-if="privacy"
        class="flex-wrap justify-center gap-2"
        size="sm"
        :options="visibilityOptions"
        :active="privacy.profile_visibility"
        :disabled="saving"
        @select="save('profile_visibility', $event)"
      />
      <div v-else-if="!error" class="skeleton h-8 w-56"></div>
    </SettingCard>
    <SettingCard
      v-for="toggle in privacyToggles"
      :key="toggle.field"
      class="mt-4"
      :title="toggle.label"
      :hint="toggle.hint"
    >
      <BaseSwitcher
        v-if="privacy"
        class="flex-wrap justify-center gap-2 shrink-0"
        size="sm"
        :options="onOffOptions"
        :active="privacy[toggle.field]"
        :disabled="saving"
        @select="save(toggle.field, $event)"
      />
      <div v-else-if="!error" class="skeleton h-8 w-28"></div>
    </SettingCard>
    <p v-if="error" class="text-error text-sm mt-4 text-center">{{ error }}</p>

    <ChatProtectionSetting class="mt-4" />
  </div>
</template>

<script>
import BaseSwitcher from '@/components/common/BaseSwitcher.vue'
import ChatProtectionSetting from '@/components/settings/ChatProtectionSetting.vue'
import SettingCard from '@/components/settings/SettingCard.vue'
import profilesApi from '@/api/profiles.js'
import { onOffOptions, privacyToggles, visibilityOptions } from '@/data/settings.js'

export default {
  name: 'PrivacySettings',
  components: { BaseSwitcher, ChatProtectionSetting, SettingCard },
  data() {
    return {
      onOffOptions,
      privacyToggles,
      visibilityOptions,
      privacy: null,
      saving: false,
      error: null,
    }
  },
  async created() {
    try {
      this.privacy = await profilesApi.privacy()
    } catch {
      this.error = 'Einstellungen konnten nicht geladen werden.'
    }
  },
  methods: {
    async save(field, value) {
      const previous = this.privacy[field]
      this.privacy[field] = value
      this.saving = true
      this.error = null
      try {
        await profilesApi.updatePrivacy({ [field]: value })
      } catch (error) {
        this.error = error.detail ?? 'Speichern fehlgeschlagen.'
        this.privacy[field] = previous
      } finally {
        this.saving = false
      }
    },
  },
}
</script>

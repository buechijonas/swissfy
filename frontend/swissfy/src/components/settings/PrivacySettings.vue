<template>
  <div class="mb-10">
    <h3 class="text-xl my-4">{{ $t('privacy.title') }}</h3>
    <SettingCard
      :title="$t('privacy.profileVisibility')"
      :hint="$t('privacy.profileVisibilityHint')"
    >
      <SelectMenu
        v-if="privacy"
        :model-value="privacy.profile_visibility"
        :options="visibilityOptions"
        :label="$t('privacy.profileVisibility')"
        :disabled="busy"
        @update:model-value="save('profile_visibility', $event)"
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
        :disabled="busy"
        @select="save(toggle.field, $event)"
      />
      <div v-else-if="!error" class="skeleton h-8 w-28"></div>
    </SettingCard>
    <ErrorText :message="error" class="mt-4 text-center" />

    <ChatProtectionSetting class="mt-4" />
  </div>
</template>

<script>
import ErrorText from '@core/components/ErrorText.vue'
import SelectMenu from '@core/components/SelectMenu.vue'
import asyncActionMixin from '@core/mixins/asyncActionMixin.js'
import BaseSwitcher from '@/components/common/BaseSwitcher.vue'
import ChatProtectionSetting from '@/components/settings/ChatProtectionSetting.vue'
import SettingCard from '@/components/settings/SettingCard.vue'
import profilesApi from '@/api/profiles.js'
import { onOffOptions, privacyToggles, visibilityOptions } from '@/data/settings.js'
import { t } from '@/i18n.js'

export default {
  name: 'PrivacySettings',
  mixins: [asyncActionMixin],
  components: { BaseSwitcher, ChatProtectionSetting, ErrorText, SelectMenu, SettingCard },
  data() {
    return {
      privacy: null,
    }
  },
  computed: {
    onOffOptions,
    privacyToggles,
    visibilityOptions,
  },
  async created() {
    try {
      this.privacy = await profilesApi.privacy()
    } catch {
      this.error = t('privacy.loadFailed')
    }
  },
  methods: {
    async save(field, value) {
      const previous = this.privacy[field]
      this.privacy[field] = value
      await this.runAction(
        () => profilesApi.updatePrivacy({ [field]: value }),
        t('common.saveFailed'),
      )
      if (this.error) this.privacy[field] = previous
    },
  },
}
</script>

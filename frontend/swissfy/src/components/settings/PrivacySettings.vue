<template>
  <div class="mb-10">
    <h3 class="my-4 text-xl">{{ $t('privacy.title') }}</h3>
    <SettingCard
      :title="$t('privacy.profileVisibility')"
      :hint="$t('privacy.profileVisibilityHint')"
    >
      <SelectMenu
        v-if="privacy"
        :model-value="privacy.profile_visibility"
        :options="visibilityOptions"
        :label="$t('privacy.profileVisibility')"
        :disabled="action.busy"
        @update:model-value="save('profile_visibility', $event)"
      />
      <div v-else-if="!action.error" class="h-8 w-56 skeleton"></div>
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
        class="shrink-0 flex-wrap justify-center gap-2"
        size="sm"
        :options="onOffOptions"
        :active="privacy[toggle.field]"
        :disabled="action.busy"
        @select="save(toggle.field, $event)"
      />
      <div v-else-if="!action.error" class="h-8 w-28 skeleton"></div>
    </SettingCard>
    <ErrorText :message="action.error" class="mt-4 text-center" />

    <ChatProtectionSetting class="mt-4" />
  </div>
</template>

<script>
import ErrorText from '@core/components/ErrorText.vue'
import SelectMenu from '@core/components/SelectMenu.vue'
import { useAsyncAction } from '@core/composables/asyncAction.js'
import profilesApi from '@/api/profiles.js'
import BaseSwitcher from '@/components/common/BaseSwitcher.vue'
import ChatProtectionSetting from '@/components/settings/ChatProtectionSetting.vue'
import SettingCard from '@/components/settings/SettingCard.vue'
import { onOffOptions, privacyToggles, visibilityOptions } from '@/data/settings.js'
import { t } from '@/i18n.js'

export default {
  name: 'PrivacySettings',
  components: { BaseSwitcher, ChatProtectionSetting, ErrorText, SelectMenu, SettingCard },
  data() {
    return {
      action: useAsyncAction(),
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
      this.action.error = t('privacy.loadFailed')
    }
  },
  methods: {
    async save(field, value) {
      const previous = this.privacy[field]
      this.privacy[field] = value
      await this.action.run(
        () => profilesApi.updatePrivacy({ [field]: value }),
        t('common.saveFailed'),
      )
      if (this.action.error) this.privacy[field] = previous
    },
  },
}
</script>

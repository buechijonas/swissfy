<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div
    class="flex max-h-[calc(100dvh-var(--mobile-chrome-height))] flex-col overflow-y-auto px-6 pb-8 lg:max-h-none lg:flex-1 lg:overflow-y-visible"
  >
    <div class="mx-auto w-full max-w-150 sm:pt-4">
      <div v-if="!authStore.ready" class="mb-10">
        <div class="mb-2 h-10 w-full skeleton"></div>
        <div class="my-5 h-5 w-24 skeleton"></div>
        <div class="h-24 w-full skeleton rounded-box"></div>
      </div>

      <template v-else>
        <BaseTabs :tabs="tabs" :active="activeTab" />

        <GeneralSettings v-if="activeTab === 'general'" />

        <PrivacySettings v-else-if="activeTab === 'privacy'" />

        <div v-else-if="activeTab === 'profile'" class="mb-10">
          <ProfilePictures />
          <ProfileAbout />
        </div>

        <div v-else-if="activeTab === 'groups'" class="mb-10">
          <h3 class="my-4 text-xl">{{ $t('settingsView.groups') }}</h3>
          <GroupManager />
        </div>

        <WellbeingSettings v-else-if="activeTab === 'wellbeing'" />

        <DisplaySettings v-else />
      </template>
    </div>
  </div>
  <BaseFooter />
</template>

<script>
import { mapStores } from 'pinia'
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import BaseTabs from '@/components/common/BaseTabs.vue'
import GroupManager from '@/components/posts/GroupManager.vue'
import DisplaySettings from '@/components/settings/DisplaySettings.vue'
import GeneralSettings from '@/components/settings/GeneralSettings.vue'
import PrivacySettings from '@/components/settings/PrivacySettings.vue'
import ProfileAbout from '@/components/settings/ProfileAbout.vue'
import ProfilePictures from '@/components/settings/ProfilePictures.vue'
import WellbeingSettings from '@/components/settings/WellbeingSettings.vue'
import { t } from '@/i18n.js'
import { useAuthStore } from '@/stores/auth.js'

export default {
  name: 'SettingsView',
  components: {
    BaseBreadcrumbs,
    BaseFooter,
    BaseTabs,
    DisplaySettings,
    GeneralSettings,
    GroupManager,
    PrivacySettings,
    ProfileAbout,
    ProfilePictures,
    WellbeingSettings,
  },
  computed: {
    breadcrumbs() {
      return [{ label: t('settingsView.title'), to: '/' }]
    },
    ...mapStores(useAuthStore),
    tabs() {
      return [
        { key: 'general', label: t('settingsView.general') },
        ...(this.authStore.isAuthenticated
          ? [
              { key: 'privacy', label: t('settingsView.privacy') },
              { key: 'profile', label: t('settingsView.profile') },
              { key: 'groups', label: t('settingsView.groups') },
            ]
          : []),
        { key: 'display', label: t('settingsView.display') },
        { key: 'wellbeing', label: t('settingsView.wellbeing') },
      ]
    },
    activeTab() {
      const tab = this.$route.query.tab
      return this.tabs.some(({ key }) => key === tab) ? tab : this.tabs[0].key
    },
  },
}
</script>

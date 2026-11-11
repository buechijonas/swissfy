<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div
    class="flex flex-col pb-8 px-6 max-h-[calc(100dvh-var(--mobile-chrome-height))] overflow-y-auto lg:max-h-none lg:overflow-y-visible lg:flex-1"
  >
    <div class="mx-auto w-full max-w-150 sm:pt-4">
      <div v-if="!authStore.ready" class="mb-10">
        <div class="skeleton mb-2 h-10 w-full"></div>
        <div class="skeleton my-5 h-5 w-24"></div>
        <div class="skeleton h-24 w-full rounded-box"></div>
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
          <h3 class="text-xl my-4">Gruppen</h3>
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
  data() {
    return {
      breadcrumbs: [{ label: 'Einstellungen', to: '/' }],
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
              { key: 'privacy', label: 'Datenschutz' },
              { key: 'profile', label: 'Profil' },
              { key: 'groups', label: 'Gruppen' },
            ]
          : []),
        { key: 'display', label: 'Darstellung' },
        { key: 'wellbeing', label: 'Wohlbefinden' },
      ]
    },
    activeTab() {
      const tab = this.$route.query.tab
      return this.tabs.some((t) => t.key === tab) ? tab : this.tabs[0].key
    },
  },
}
</script>

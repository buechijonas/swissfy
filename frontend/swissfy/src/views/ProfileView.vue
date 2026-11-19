<template>
  <BaseBreadcrumbs :items="breadcrumbs">
    <template v-if="ownProfile" #actions>
      <AddButton :label="$t('profile.post')" :loading="loading" @click="$refs.composer.open()" />
    </template>
  </BaseBreadcrumbs>
  <div
    class="flex max-h-[calc(100dvh-var(--mobile-chrome-height))] flex-col overflow-y-auto px-6 pb-8 lg:max-h-none lg:flex-1 lg:overflow-y-visible"
    :class="{ 'max-sm:pb-0': timeline }"
  >
    <div class="mx-auto w-full max-w-150 sm:pt-4">
      <BaseCard v-if="loading" class="p-6">
        <div class="flex items-center justify-center gap-4">
          <div class="size-20 skeleton rounded-full"></div>
          <div class="flex flex-col gap-2">
            <div class="h-5 w-40 skeleton"></div>
            <div class="h-4 w-24 skeleton"></div>
          </div>
        </div>
        <div class="mt-6 h-16 w-full skeleton"></div>
      </BaseCard>

      <BaseCard v-else-if="error" class="p-6">
        <p class="text-app-muted">{{ error }}</p>
      </BaseCard>

      <ProfileHeader
        v-else
        :key="profile.username"
        v-model:profile="profile"
        @open-story="$refs.storyViewer.open()"
      />

      <template v-if="!loading && !error && tabs.length">
        <BaseTabs class="border-t-0" :tabs="tabs" :active="activeTab" />
        <ProfileAbout v-if="activeTab === 'about'" :profile="profile" />
        <ProfileAchievements
          v-else-if="activeTab === 'achievements'"
          :key="`${profile.username}-achievements`"
          :username="profile.username"
        />
        <ProfileAlbums
          v-else-if="activeTab === 'albums'"
          :key="`${profile.username}-albums`"
          :username="profile.username"
          :editable="profile.is_self"
        />
        <ProfileStatus
          v-else-if="activeTab === 'status'"
          :key="`${profile.username}-status`"
          :username="profile.username"
        />
        <ProfilePosts v-else :profile="profile" :timeline="timeline" />
      </template>
    </div>
  </div>
  <CreateDialog v-if="profile?.is_self" ref="composer" />
  <StoryViewer
    v-if="profile"
    ref="storyViewer"
    :stories="profile.stories ?? []"
    :author="profile"
    @deleted="refreshProfile"
    @closed="refreshProfile"
  />
  <BaseFooter />
</template>

<script>
import { mapStores } from 'pinia'
import BaseCard from '@core/components/BaseCard.vue'
import profilesApi from '@/api/profiles.js'
import ProfileAchievements from '@/components/achievements/ProfileAchievements.vue'
import ProfileAlbums from '@/components/albums/ProfileAlbums.vue'
import AddButton from '@/components/common/AddButton.vue'
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import BaseTabs from '@/components/common/BaseTabs.vue'
import ProfileStatus from '@/components/moderation/ProfileStatus.vue'
import CreateDialog from '@/components/posts/CreateDialog.vue'
import StoryViewer from '@/components/posts/StoryViewer.vue'
import ProfileAbout from '@/components/profile/ProfileAbout.vue'
import ProfileHeader from '@/components/profile/ProfileHeader.vue'
import ProfilePosts from '@/components/profile/ProfilePosts.vue'
import { t } from '@/i18n.js'
import { useAuthStore } from '@/stores/auth.js'

function profileTabs() {
  return [
    { key: 'activities', label: t('profile.activity'), icon: 'list-timeline' },
    { key: 'tiles', label: t('profile.grid'), icon: 'grid' },
    { key: 'albums', label: t('profile.albums'), icon: 'gallery' },
    { key: 'about', label: t('profile.about'), icon: 'info' },
    { key: 'achievements', label: t('profile.achievements'), icon: 'trophy' },
    { key: 'status', label: t('profile.status'), icon: 'map-marker-smile' },
  ]
}

function moderationTabs() {
  return profileTabs().filter((tab) => ['tiles', 'activities', 'status'].includes(tab.key))
}

export default {
  name: 'ProfileView',
  components: {
    AddButton,
    BaseBreadcrumbs,
    BaseCard,
    BaseFooter,
    BaseTabs,
    CreateDialog,
    ProfileAbout,
    ProfileAchievements,
    ProfileAlbums,
    ProfileHeader,
    ProfilePosts,
    ProfileStatus,
    StoryViewer,
  },
  data() {
    return {
      profile: null,
      loading: true,
      error: null,
    }
  },
  computed: {
    ...mapStores(useAuthStore),
    username() {
      return this.$route.params.username
    },
    ownProfile() {
      if (this.profile && !this.loading) return this.profile.is_self
      return !this.username || this.username === this.authStore.user?.username
    },
    tabs() {
      if (!this.profile?.can_view) return this.profile?.can_view_warnings ? moderationTabs() : []
      return profileTabs().filter((tab) => tab.key !== 'status' || this.profile.can_view_warnings)
    },
    activeTab() {
      const tab = this.$route.query.tab
      return this.tabs.some(({ key }) => key === tab)
        ? tab
        : (this.tabs[0]?.key ?? profileTabs()[0].key)
    },
    timeline() {
      return this.activeTab === 'activities'
    },
    breadcrumbs() {
      return this.username
        ? [{ label: this.username, to: `/profile/${this.username}` }]
        : [{ label: t('profile.profile'), to: '/profile' }]
    },
  },
  watch: {
    username: {
      immediate: true,
      handler() {
        this.loadProfile()
      },
    },
  },
  methods: {
    async loadProfile() {
      this.loading = true
      this.error = null
      try {
        this.profile = await profilesApi.get(this.username)
      } catch (error) {
        this.error = error.status === 404 ? t('profile.notFound') : t('profile.loadFailed')
      } finally {
        this.loading = false
      }
    },
    async refreshProfile() {
      const profile = await profilesApi.get(this.username).catch(() => null)
      if (profile) this.profile = profile
    },
  },
}
</script>

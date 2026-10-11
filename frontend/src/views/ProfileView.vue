<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div
    class="flex flex-col pb-8 px-6 max-h-[calc(100dvh-96px)] overflow-y-auto lg:max-h-none lg:overflow-y-visible lg:flex-1"
    :class="{ 'max-sm:pb-0': timeline }"
  >
    <div class="mx-auto w-full max-w-150 sm:pt-4">
      <BaseCard v-if="loading" class="p-6">
        <div class="flex items-center justify-center gap-4">
          <div class="skeleton size-20 rounded-full"></div>
          <div class="flex flex-col gap-2">
            <div class="skeleton h-5 w-40"></div>
            <div class="skeleton h-4 w-24"></div>
          </div>
        </div>
        <div class="skeleton mt-6 h-16 w-full"></div>
      </BaseCard>

      <BaseCard v-else-if="error" class="p-6">
        <p class="text-swissfy-muted">{{ error }}</p>
      </BaseCard>

      <BaseCard v-else class="p-6">
        <div class="flex items-center justify-center gap-4">
          <img class="size-20 shrink-0" :src="avatarSrc" alt="" />
          <div class="flex flex-col min-w-0">
            <span class="flex min-w-0 items-center gap-2">
              <CipherText v-if="!profile.can_view" :length="10" class="text-lg font-bold" />
              <span v-else class="text-lg font-bold truncate">{{
                fullName || profile.username
              }}</span>
              <RoleBadge :role="profile.role" />
            </span>
            <span class="text-swissfy-muted truncate">@{{ profile.username }}</span>
          </div>
        </div>

        <div class="grid grid-cols-3 gap-4 mt-6 text-center">
          <div class="flex flex-col items-center gap-2">
            <CipherText v-if="!profile.can_view" class="text-xl font-bold" />
            <span v-else class="text-xl font-bold">{{ profile.follower_count }}</span>
            <span class="text-swissfy-muted text-sm">Follower</span>
            <BaseButton
              v-if="!profile.is_self"
              size="sm"
              block
              :variant="profile.is_following || profile.follow_requested ? 'neutral' : 'primary'"
              :disabled="busy"
              @click="toggleFollow"
            >
              {{ followLabel }}
            </BaseButton>
          </div>
          <div class="flex flex-col items-center gap-2">
            <CipherText v-if="!profile.can_view" class="text-xl font-bold" />
            <span v-else class="text-xl font-bold">{{ profile.following_count }}</span>
            <span class="text-swissfy-muted text-sm">Gefolgt</span>
            <BaseButton
              v-if="!profile.is_self"
              size="sm"
              block
              variant="primary"
              :to="profile.can_chat ? `/chats/${encodeURIComponent(profile.username)}` : null"
              :disabled="!profile.can_chat"
            >
              Chat
            </BaseButton>
          </div>
          <div class="flex flex-col items-center gap-2">
            <CipherText v-if="!profile.can_view" class="text-xl font-bold" />
            <span v-else class="text-xl font-bold">{{ profile.friend_count }}</span>
            <span class="text-swissfy-muted text-sm">Freunde</span>
            <BaseButton
              v-if="canRequestFriendship"
              size="sm"
              block
              variant="primary"
              :disabled="busy || profile.friend_request_sent"
              @click="sendFriendRequest"
            >
              {{ profile.friend_request_sent ? 'Angefragt' : 'Anfragen' }}
            </BaseButton>
          </div>
        </div>

        <p
          v-if="!profile.can_view"
          class="flex items-center justify-center gap-2 text-swissfy-muted text-sm mt-6"
        >
          <AppIcon name="lock" size="sm" />
          Dieses Profil ist privat.
        </p>

        <p v-if="actionError" class="text-error text-sm mt-4 text-center">{{ actionError }}</p>
      </BaseCard>

      <template v-if="!loading && !error && tabs.length">
        <BaseTabs class="border-t-0" :tabs="tabs" :active="activeTab" />
        <BaseCard v-if="activeTab === 'about'" class="p-6 border-t-0">
          <dl v-if="profile.birthdate" class="flex justify-between gap-4">
            <dt class="text-swissfy-muted">Geburtsdatum</dt>
            <dd>{{ formatDate(profile.birthdate) }}</dd>
          </dl>
          <p v-else class="text-swissfy-muted">Keine Angaben.</p>
        </BaseCard>
        <ProfileStatus
          v-else-if="activeTab === 'status'"
          :key="`${profile.username}-status`"
          :username="profile.username"
        />
        <PostList
          v-else-if="activeTab === 'tiles' || activeTab === 'activities'"
          :key="`${profile.username}-${activeTab}`"
          class="mt-4"
          :class="{ 'max-sm:mt-0': timeline }"
          :url="postsUrl"
          :grid="activeTab === 'tiles'"
          :edge-to-edge="timeline"
          :empty-text="activeTab === 'tiles' ? 'Noch keine Bilder.' : 'Noch keine Posts.'"
        />
      </template>
    </div>
  </div>
  <BaseFooter />
</template>

<script>
import AppIcon from '@/components/common/AppIcon.vue'
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import BaseTabs from '@/components/common/BaseTabs.vue'
import CipherText from '@/components/common/CipherText.vue'
import RoleBadge from '@/components/common/RoleBadge.vue'
import PostList from '@/components/posts/PostList.vue'
import ProfileStatus from '@/components/moderation/ProfileStatus.vue'
import { icons } from '@/assets/icons.js'
import { avatars } from '@/assets/images.js'
import { apiFetch, extractErrorMessage } from '@/lib/api.js'
import { formatDate } from '@/lib/time.js'

const TABS = [
  { key: 'tiles', label: 'Kachel', icon: 'grid' },
  { key: 'activities', label: 'Aktivitäten', icon: 'list-timeline' },
  { key: 'albums', label: 'Alben', icon: 'gallery' },
  { key: 'about', label: 'Über mich', icon: 'info' },
  { key: 'status', label: 'Status', icon: 'map-marker-smile' },
]
const MODERATION_TABS = TABS.filter((tab) => ['tiles', 'activities', 'status'].includes(tab.key))

export default {
  name: 'ProfileView',
  components: {
    AppIcon,
    BaseBreadcrumbs,
    BaseButton,
    BaseCard,
    BaseFooter,
    BaseTabs,
    CipherText,
    PostList,
    ProfileStatus,
    RoleBadge,
  },
  data() {
    return {
      profile: null,
      loading: true,
      error: null,
      busy: false,
      actionError: null,
    }
  },
  computed: {
    username() {
      return this.$route.params.username
    },
    tabs() {
      if (!this.profile?.can_view) return this.profile?.can_view_warnings ? MODERATION_TABS : []
      return TABS.filter((tab) => tab.key !== 'status' || this.profile.can_view_warnings)
    },
    activeTab() {
      const tab = this.$route.query.tab
      return this.tabs.some((t) => t.key === tab) ? tab : (this.tabs[0]?.key ?? TABS[0].key)
    },
    timeline() {
      return this.activeTab === 'activities'
    },
    breadcrumbs() {
      return this.username
        ? [{ label: this.username, to: `/profile/${this.username}` }]
        : [{ label: 'Profil', to: '/profile' }]
    },
    apiUrl() {
      return `/api/social/profiles/${this.username ? encodeURIComponent(this.username) : 'me'}/`
    },
    avatarSrc() {
      return avatars[this.profile.avatar] ?? icons.user
    },
    postsUrl() {
      const base = `/api/posts/users/${encodeURIComponent(this.profile.username)}/`
      return this.activeTab === 'tiles' ? `${base}?images=1` : `${base}activities/`
    },
    followLabel() {
      const p = this.profile
      if (p.is_following) return 'Entfolgen'
      if (p.follow_requested) return 'Angefragt'
      return p.requires_follow_request ? 'Anfragen' : 'Folgen'
    },
    fullName() {
      return [this.profile.first_name, this.profile.last_name].filter(Boolean).join(' ')
    },
    canRequestFriendship() {
      const p = this.profile
      return !p.is_self && !p.is_friend && p.is_following && p.follows_you
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
    formatDate,
    async loadProfile() {
      this.loading = true
      this.error = null
      this.actionError = null
      const response = await apiFetch(this.apiUrl)
      if (response.ok) {
        this.profile = await response.json()
      } else {
        this.error =
          response.status === 404 ? 'Profil nicht gefunden.' : 'Profil konnte nicht geladen werden.'
      }
      this.loading = false
    },
    async runAction(path, method, fallback) {
      this.busy = true
      this.actionError = null
      try {
        const response = await apiFetch(`${this.apiUrl}${path}`, { method })
        const data = await response.json().catch(() => null)
        if (response.ok) {
          this.profile = data
        } else {
          this.actionError = extractErrorMessage(data, fallback)
        }
      } finally {
        this.busy = false
      }
    },
    toggleFollow() {
      const method = this.profile.is_following || this.profile.follow_requested ? 'DELETE' : 'POST'
      return this.runAction('follow/', method, 'Aktion fehlgeschlagen.')
    },
    sendFriendRequest() {
      return this.runAction('friend-request/', 'POST', 'Anfrage fehlgeschlagen.')
    },
  },
}
</script>

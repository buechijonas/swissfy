<template>
  <BaseBreadcrumbs :items="breadcrumbs">
    <template v-if="profile?.is_self" #actions>
      <AddButton label="Posten" @click="$refs.composer.open()" />
    </template>
  </BaseBreadcrumbs>
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
          <UserAvatar class="size-20" :user="profile" />
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
          <BaseButton
            v-if="profile.is_self"
            shape="square"
            class="shrink-0"
            to="/settings?tab=profile"
            title="Bearbeiten"
          >
            <AppIcon name="pencil" alt="Bearbeiten" />
          </BaseButton>
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
              <AppIcon :name="followIcon" />
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
              <AppIcon name="comments" />
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
              <AppIcon :name="profile.friend_request_sent ? 'clock' : 'users'" />
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
        <ProfileAchievements
          v-else-if="activeTab === 'achievements'"
          :key="`${profile.username}-achievements`"
          :username="profile.username"
        />
        <ProfileStatus
          v-else-if="activeTab === 'status'"
          :key="`${profile.username}-status`"
          :username="profile.username"
        />
        <PostList
          v-else-if="postList"
          :key="`${profile.username}-${activeTab}-${postsVersion}`"
          class="mt-4"
          :class="{ 'max-sm:mt-0': timeline }"
          :url="postsUrl"
          :grid="!timeline"
          :edge-to-edge="timeline"
          :empty-text="postList.emptyText"
        />
      </template>
    </div>
  </div>
  <PostComposer v-if="profile?.is_self" ref="composer" @created="showOwnPosts" />
  <BaseFooter />
</template>

<script>
import AddButton from '@/components/common/AddButton.vue'
import AppIcon from '@/components/common/AppIcon.vue'
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import BaseTabs from '@/components/common/BaseTabs.vue'
import CipherText from '@/components/common/CipherText.vue'
import RoleBadge from '@/components/common/RoleBadge.vue'
import ProfileAchievements from '@/components/achievements/ProfileAchievements.vue'
import PostComposer from '@/components/posts/PostComposer.vue'
import PostList from '@/components/posts/PostList.vue'
import ProfileStatus from '@/components/moderation/ProfileStatus.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import { apiFetch, extractErrorMessage } from '@/lib/api.js'
import { formatDate } from '@/lib/time.js'

const TABS = [
  { key: 'activities', label: 'Aktivitäten', icon: 'list-timeline' },
  { key: 'tiles', label: 'Kachel', icon: 'grid' },
  { key: 'reels', label: 'Reels', icon: 'clapperboard-play' },
  { key: 'albums', label: 'Alben', icon: 'gallery' },
  { key: 'about', label: 'Über mich', icon: 'info' },
  { key: 'achievements', label: 'Erfolge', icon: 'trophy' },
  { key: 'status', label: 'Status', icon: 'map-marker-smile' },
]
const POST_LISTS = {
  tiles: { query: '?images=1', emptyText: 'Noch keine Bilder.' },
  reels: { query: '?videos=1', emptyText: 'Noch keine Reels.' },
  activities: { query: 'activities/', emptyText: 'Noch keine Posts.' },
}
const MODERATION_TABS = TABS.filter((tab) => ['tiles', 'activities', 'status'].includes(tab.key))

export default {
  name: 'ProfileView',
  components: {
    AddButton,
    AppIcon,
    BaseBreadcrumbs,
    BaseButton,
    BaseCard,
    BaseFooter,
    BaseTabs,
    CipherText,
    PostComposer,
    PostList,
    ProfileAchievements,
    ProfileStatus,
    RoleBadge,
    UserAvatar,
  },
  data() {
    return {
      profile: null,
      loading: true,
      error: null,
      busy: false,
      actionError: null,
      postsVersion: 0,
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
    postList() {
      return POST_LISTS[this.activeTab]
    },
    breadcrumbs() {
      return this.username
        ? [{ label: this.username, to: `/profile/${this.username}` }]
        : [{ label: 'Profil', to: '/profile' }]
    },
    apiUrl() {
      return `/api/social/profiles/${this.username ? encodeURIComponent(this.username) : 'me'}/`
    },
    postsUrl() {
      const base = `/api/posts/users/${encodeURIComponent(this.profile.username)}/`
      return `${base}${this.postList.query}`
    },
    followLabel() {
      const p = this.profile
      if (p.is_following) return 'Entfolgen'
      if (p.follow_requested) return 'Angefragt'
      return p.requires_follow_request ? 'Anfragen' : 'Folgen'
    },
    followIcon() {
      const p = this.profile
      if (p.is_following) return 'user-minus'
      return p.follow_requested ? 'clock' : 'user-add'
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
    showOwnPosts() {
      this.postsVersion++
      this.$router.push({ query: { ...this.$route.query, tab: 'activities' } })
    },
  },
}
</script>

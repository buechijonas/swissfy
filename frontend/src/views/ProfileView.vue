<template>
  <BaseBreadcrumbs :items="breadcrumbs">
    <template v-if="ownProfile" #actions>
      <AddButton label="Posten" :loading="loading" @click="$refs.composer.open()" />
    </template>
  </BaseBreadcrumbs>
  <div
    class="flex flex-col pb-8 px-6 max-h-[calc(100dvh-var(--mobile-chrome-height))] overflow-y-auto lg:max-h-none lg:overflow-y-visible lg:flex-1"
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
          <div class="relative shrink-0">
            <button
              v-if="profile.stories?.length"
              type="button"
              class="block cursor-pointer rounded-full"
              title="Story ansehen"
              @click="$refs.storyViewer.open()"
            >
              <UserAvatar
                class="size-20"
                :user="profile"
                story-ring
                :story-seen="profile.stories.every((story) => story.seen)"
              />
            </button>
            <button
              v-else-if="profile.is_self"
              type="button"
              class="block cursor-pointer rounded-full"
              title="Story hinzufügen"
              @click="$router.push('/upload/story')"
            >
              <UserAvatar class="size-20" :user="profile" />
            </button>
            <UserAvatar v-else class="size-20" :user="profile" />
            <button
              v-if="profile.is_self && !profile.stories?.length"
              type="button"
              class="absolute -right-0.5 -bottom-0.5 flex size-6 cursor-pointer items-center justify-center rounded-full bg-primary text-primary-content ring-2 ring-base-100"
              title="Story hinzufügen"
              @click="$router.push('/upload/story')"
            >
              <AppIcon name="plus" alt="Story hinzufügen" class="size-3!" />
            </button>
          </div>
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
            <RouterLink
              v-if="profile.can_view"
              :to="connectionLink('followers')"
              class="flex flex-col items-center gap-2 hover:underline"
            >
              <span class="text-xl font-bold">{{ profile.follower_count }}</span>
              <span class="text-swissfy-muted text-sm">Follower</span>
            </RouterLink>
            <template v-else>
              <CipherText class="text-xl font-bold" />
              <span class="text-swissfy-muted text-sm">Follower</span>
            </template>
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
            <RouterLink
              v-if="profile.can_view"
              :to="connectionLink('following')"
              class="flex flex-col items-center gap-2 hover:underline"
            >
              <span class="text-xl font-bold">{{ profile.following_count }}</span>
              <span class="text-swissfy-muted text-sm">Gefolgt</span>
            </RouterLink>
            <template v-else>
              <CipherText class="text-xl font-bold" />
              <span class="text-swissfy-muted text-sm">Gefolgt</span>
            </template>
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
            <RouterLink
              v-if="profile.can_view"
              :to="connectionLink('friends')"
              class="flex flex-col items-center gap-2 hover:underline"
            >
              <span class="text-xl font-bold">{{ profile.friend_count }}</span>
              <span class="text-swissfy-muted text-sm">Freunde</span>
            </RouterLink>
            <template v-else>
              <CipherText class="text-xl font-bold" />
              <span class="text-swissfy-muted text-sm">Freunde</span>
            </template>
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
        <BaseCard v-if="activeTab === 'about'" class="p-6 border-t-0 flex flex-col gap-6">
          <p v-if="profile.biography" class="whitespace-pre-line break-words">
            {{ profile.biography }}
          </p>
          <dl v-if="profile.birthdate" class="flex justify-between gap-4">
            <dt class="text-swissfy-muted">Geburtsdatum</dt>
            <dd>{{ formatDate(profile.birthdate) }}</dd>
          </dl>
          <section v-for="favorite in favorites" :key="favorite.kind">
            <h4 class="text-swissfy-muted mb-2">{{ favorite.label }}</h4>
            <ul class="grid grid-cols-3 gap-4">
              <li v-for="item in profile[favorite.field]" :key="item.id" class="min-w-0">
                <FavoriteCover :item="item" :icon="favorite.icon" />
                <p class="text-sm truncate mt-2" :title="item.title">{{ item.title }}</p>
                <p v-if="item.year" class="text-xs text-swissfy-muted">{{ item.year }}</p>
              </li>
            </ul>
          </section>
          <LibraryCredits v-if="favorites.length" />
          <p
            v-if="!profile.biography && !profile.birthdate && !favorites.length"
            class="text-swissfy-muted"
          >
            Keine Angaben.
          </p>
        </BaseCard>
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
        <div v-if="switcher" class="flex max-sm:-mx-6 lg:mt-2 lg:justify-end">
          <BaseSwitcher
            class="join w-full lg:w-auto"
            item-class="join-item max-lg:flex-1 max-lg:rounded-none"
            :options="switcher.options"
            :active="switcher.active"
            @select="$router.replace({ query: { ...$route.query, [switcher.param]: $event } })"
          />
        </div>
        <PostList
          v-if="postList"
          :key="`${profile.username}-${activeTab}-${switcher?.active}`"
          :class="switcher ? 'lg:mt-2' : 'mt-4'"
          :url="postsUrl"
          :grid="!timeline"
          :edge-to-edge="timeline"
          :empty-text="postList.emptyText"
        />
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
import { RouterLink } from 'vue-router'
import AddButton from '@/components/common/AddButton.vue'
import AppIcon from '@/components/common/AppIcon.vue'
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import BaseSwitcher from '@/components/common/BaseSwitcher.vue'
import BaseTabs from '@/components/common/BaseTabs.vue'
import CipherText from '@/components/common/CipherText.vue'
import RoleBadge from '@/components/common/RoleBadge.vue'
import ProfileAchievements from '@/components/achievements/ProfileAchievements.vue'
import ProfileAlbums from '@/components/albums/ProfileAlbums.vue'
import CreateDialog from '@/components/posts/CreateDialog.vue'
import PostList from '@/components/posts/PostList.vue'
import StoryViewer from '@/components/posts/StoryViewer.vue'
import ProfileStatus from '@/components/moderation/ProfileStatus.vue'
import FavoriteCover from '@/components/settings/FavoriteCover.vue'
import LibraryCredits from '@/components/settings/LibraryCredits.vue'
import { favoriteKinds } from '@/data/favorites.js'
import UserAvatar from '@/components/common/UserAvatar.vue'
import { apiFetch, extractErrorMessage } from '@/lib/api.js'
import { useAuthStore } from '@/stores/auth.js'
import { formatDate } from '@/lib/time.js'

const TABS = [
  { key: 'activities', label: 'Aktivitäten', icon: 'list-timeline' },
  { key: 'tiles', label: 'Kachel', icon: 'grid' },
  { key: 'albums', label: 'Alben', icon: 'gallery' },
  { key: 'about', label: 'Über mich', icon: 'info' },
  { key: 'achievements', label: 'Erfolge', icon: 'trophy' },
  { key: 'status', label: 'Status', icon: 'map-marker-smile' },
]
const MEDIA = {
  pictures: {
    flag: 'pictures',
    label: 'Feeds',
    icon: 'picture',
    query: '?images=1',
    emptyText: 'Noch keine Feeds.',
  },
  clips: {
    flag: 'reels',
    label: 'Seeds',
    icon: 'clapperboard-play',
    query: '?videos=1',
    emptyText: 'Noch keine Seeds.',
  },
}
const ACTIVITIES = {
  feeds: {
    label: 'Feeds',
    icon: 'list-timeline',
    query: 'activities/',
    emptyText: 'Noch keine Feeds.',
  },
  comments: {
    label: 'Kommentare',
    icon: 'comments',
    query: 'activities/?comments=1',
    emptyText: 'Noch keine Kommentare.',
  },
}
const toOptions = (entries) =>
  Object.entries(entries).map(([value, { label, icon }]) => ({ value, label, icon }))
const MODERATION_TABS = TABS.filter((tab) => ['tiles', 'activities', 'status'].includes(tab.key))

export default {
  name: 'ProfileView',
  components: {
    CreateDialog,
    RouterLink,
    AddButton,
    AppIcon,
    BaseBreadcrumbs,
    BaseButton,
    BaseCard,
    BaseFooter,
    BaseSwitcher,
    BaseTabs,
    CipherText,
    FavoriteCover,
    LibraryCredits,
    PostList,
    ProfileAchievements,
    ProfileAlbums,
    ProfileStatus,
    RoleBadge,
    StoryViewer,
    UserAvatar,
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
    ownProfile() {
      if (this.profile && !this.loading) return this.profile.is_self
      return !this.username || this.username === useAuthStore().user?.username
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
    favorites() {
      return favoriteKinds.filter((favorite) => this.profile[favorite.field]?.length)
    },
    availableMedia() {
      return Object.keys(MEDIA).filter((key) => this.profile.media?.[MEDIA[key].flag])
    },
    media() {
      const requested = this.$route.query.media
      if (this.availableMedia.includes(requested)) return requested
      return this.availableMedia[0] ?? 'pictures'
    },
    activity() {
      const requested = this.$route.query.activity
      return Object.hasOwn(ACTIVITIES, requested) ? requested : 'feeds'
    },
    switcher() {
      if (this.timeline) {
        return { param: 'activity', options: toOptions(ACTIVITIES), active: this.activity }
      }
      if (this.activeTab === 'tiles' && this.availableMedia.length > 1) {
        return { param: 'media', options: toOptions(MEDIA), active: this.media }
      }
      return null
    },
    postList() {
      if (this.timeline) return ACTIVITIES[this.activity]
      return this.activeTab === 'tiles' ? MEDIA[this.media] : null
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
    connectionLink(connection) {
      return `/profile/${encodeURIComponent(this.profile.username)}/${connection}`
    },
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
    async refreshProfile() {
      const response = await apiFetch(this.apiUrl).catch(() => null)
      if (response?.ok) this.profile = await response.json()
    },
  },
}
</script>

<template>
  <BaseBreadcrumbs :items="breadcrumbs" />
  <div
    class="flex flex-col pb-8 px-6 max-h-[calc(100dvh-48px)] overflow-y-auto lg:max-h-none lg:overflow-y-visible lg:flex-1"
  >
    <div class="mx-auto w-full max-w-150">
      <h2 class="text-xl font-light my-4">Profil</h2>

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
            <span class="text-lg font-bold truncate">{{ fullName || profile.username }}</span>
            <span class="text-swissfy-muted truncate">@{{ profile.username }}</span>
          </div>
        </div>

        <div class="grid grid-cols-3 gap-4 mt-6 text-center">
          <div class="flex flex-col items-center gap-2">
            <span class="text-xl font-bold">{{ profile.follower_count ?? '–' }}</span>
            <span class="text-swissfy-muted text-sm">Follower</span>
            <BaseButton
              v-if="!profile.is_self"
              size="sm"
              :variant="profile.is_following ? 'neutral' : 'primary'"
              :disabled="busy"
              @click="toggleFollow"
            >
              {{ profile.is_following ? 'Entfolgen' : 'Folgen' }}
            </BaseButton>
          </div>
          <div class="flex flex-col items-center gap-2">
            <span class="text-xl font-bold">{{ profile.following_count ?? '–' }}</span>
            <span class="text-swissfy-muted text-sm">Gefolgt</span>
          </div>
          <div class="flex flex-col items-center gap-2">
            <span class="text-xl font-bold">{{ profile.friend_count ?? '–' }}</span>
            <span class="text-swissfy-muted text-sm">Freunde</span>
            <BaseButton
              v-if="canRequestFriendship"
              size="sm"
              variant="primary"
              :disabled="busy || profile.friend_request_sent"
              @click="sendFriendRequest"
            >
              {{ profile.friend_request_sent ? 'Angefragt' : 'Anfragen' }}
            </BaseButton>
          </div>
        </div>

        <p v-if="!profile.can_view" class="text-swissfy-muted text-sm mt-6 text-center">
          Dieses Profil ist privat.
        </p>

        <p v-if="actionError" class="text-error text-sm mt-4 text-center">{{ actionError }}</p>
      </BaseCard>
    </div>
  </div>
  <BaseFooter />
</template>

<script>
import BaseBreadcrumbs from '@/components/common/BaseBreadcrumbs.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseFooter from '@/components/common/BaseFooter.vue'
import { icons } from '@/assets/icons.js'
import { avatars } from '@/assets/images.js'
import { apiFetch, extractErrorMessage } from '@/lib/api.js'

export default {
  name: 'ProfileView',
  components: { BaseBreadcrumbs, BaseButton, BaseCard, BaseFooter },
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
      const method = this.profile.is_following ? 'DELETE' : 'POST'
      return this.runAction('follow/', method, 'Aktion fehlgeschlagen.')
    },
    sendFriendRequest() {
      return this.runAction('friend-request/', 'POST', 'Anfrage fehlgeschlagen.')
    },
  },
}
</script>

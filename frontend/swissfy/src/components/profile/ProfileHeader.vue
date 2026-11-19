<template>
  <BaseCard class="p-6">
    <div class="flex items-center justify-center gap-4">
      <div class="relative shrink-0">
        <button
          v-if="profile.stories?.length"
          type="button"
          class="block cursor-pointer rounded-full"
          :title="$t('profile.viewStory')"
          @click="$emit('open-story')"
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
          :title="$t('profile.addStory')"
          @click="$router.push('/upload/story')"
        >
          <UserAvatar class="size-20" :user="profile" />
        </button>
        <UserAvatar v-else class="size-20" :user="profile" />
        <button
          v-if="profile.is_self && !profile.stories?.length"
          type="button"
          class="absolute -right-0.5 -bottom-0.5 flex size-6 cursor-pointer items-center justify-center rounded-full bg-primary text-primary-content ring-2 ring-base-100"
          :title="$t('profile.addStory')"
          @click="$router.push('/upload/story')"
        >
          <AppIcon name="plus" :alt="$t('profile.addStory')" class="size-3!" />
        </button>
      </div>
      <div class="flex min-w-0 flex-col">
        <span class="flex min-w-0 items-center gap-2">
          <CipherText v-if="!profile.can_view" :length="10" class="text-lg font-bold" />
          <span v-else class="truncate text-lg font-bold">{{ profile.display_name }}</span>
          <RoleBadge :role="profile.role" />
        </span>
        <span class="truncate text-app-muted">@{{ profile.username }}</span>
      </div>
      <BaseButton
        v-if="profile.is_self"
        shape="square"
        class="shrink-0"
        to="/settings?tab=profile"
        :title="$t('common.edit')"
      >
        <AppIcon name="pencil" :alt="$t('common.edit')" />
      </BaseButton>
    </div>

    <div class="mt-6 grid grid-cols-3 gap-4 text-center">
      <ProfileStat
        :count="profile.follower_count"
        :label="$t('profile.followers')"
        :to="connectionLink('followers')"
        :visible="profile.can_view"
      >
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
      </ProfileStat>
      <ProfileStat
        :count="profile.following_count"
        :label="$t('profile.following')"
        :to="connectionLink('following')"
        :visible="profile.can_view"
      >
        <BaseButton
          v-if="!profile.is_self"
          size="sm"
          block
          variant="primary"
          :to="profile.can_chat ? `/chats/${encodeURIComponent(profile.username)}` : null"
          :disabled="!profile.can_chat"
        >
          <AppIcon name="comments" />
          {{ $t('profile.chat') }}
        </BaseButton>
      </ProfileStat>
      <ProfileStat
        :count="profile.friend_count"
        :label="$t('profile.friends')"
        :to="connectionLink('friends')"
        :visible="profile.can_view"
      >
        <BaseButton
          v-if="canRequestFriendship"
          size="sm"
          block
          variant="primary"
          :disabled="busy || profile.friend_request_sent"
          @click="sendFriendRequest"
        >
          <AppIcon :name="profile.friend_request_sent ? 'clock' : 'users'" />
          {{ profile.friend_request_sent ? $t('profile.requested') : $t('profile.request') }}
        </BaseButton>
      </ProfileStat>
    </div>

    <p
      v-if="!profile.can_view"
      class="mt-6 flex items-center justify-center gap-2 text-sm text-app-muted"
    >
      <AppIcon name="lock" size="sm" />
      {{ $t('profile.private') }}
    </p>

    <ErrorText :message="error" class="mt-4 text-center" />
  </BaseCard>
</template>

<script>
import AppIcon from '@core/components/AppIcon.vue'
import BaseButton from '@core/components/BaseButton.vue'
import BaseCard from '@core/components/BaseCard.vue'
import ErrorText from '@core/components/ErrorText.vue'
import profilesApi from '@/api/profiles.js'
import CipherText from '@/components/common/CipherText.vue'
import RoleBadge from '@/components/common/RoleBadge.vue'
import UserAvatar from '@/components/common/UserAvatar.vue'
import ProfileStat from '@/components/profile/ProfileStat.vue'
import { t } from '@/i18n.js'

export default {
  name: 'ProfileHeader',
  components: {
    AppIcon,
    BaseButton,
    BaseCard,
    CipherText,
    ErrorText,
    ProfileStat,
    RoleBadge,
    UserAvatar,
  },
  props: {
    profile: { type: Object, required: true },
  },
  emits: ['update:profile', 'open-story'],
  data() {
    return { busy: false, error: null }
  },
  computed: {
    followLabel() {
      const p = this.profile
      if (p.is_following) return t('profile.unfollow')
      if (p.follow_requested) return t('profile.requested')
      return p.requires_follow_request ? t('profile.request') : t('profile.follow')
    },
    followIcon() {
      const p = this.profile
      if (p.is_following) return 'user-minus'
      return p.follow_requested ? 'clock' : 'user-add'
    },
    canRequestFriendship() {
      const p = this.profile
      return !p.is_self && !p.is_friend && p.is_following && p.follows_you
    },
  },
  methods: {
    connectionLink(connection) {
      return `/profile/${encodeURIComponent(this.profile.username)}/${connection}`
    },
    async runAction(action, fallback) {
      this.busy = true
      this.error = null
      try {
        this.$emit('update:profile', await action())
      } catch (error) {
        this.error = error.detail ?? fallback
      } finally {
        this.busy = false
      }
    },
    toggleFollow() {
      const { username, is_following, follow_requested } = this.profile
      const leave = is_following || follow_requested
      return this.runAction(
        () => (leave ? profilesApi.unfollow(username) : profilesApi.follow(username)),
        t('profile.actionFailed'),
      )
    },
    sendFriendRequest() {
      return this.runAction(
        () => profilesApi.requestFriendship(this.profile.username),
        t('profile.requestFailed'),
      )
    },
  },
}
</script>

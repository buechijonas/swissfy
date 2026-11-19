<template>
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
    :key="`${profile.username}-${timeline}-${switcher?.active}`"
    :class="switcher ? 'lg:mt-2' : 'mt-4'"
    :url="url"
    :grid="!timeline"
    :edge-to-edge="timeline"
    :empty-text="kind.emptyText"
  />
</template>

<script>
import map from 'lodash-es/map'
import postsApi from '@/api/posts.js'
import BaseSwitcher from '@/components/common/BaseSwitcher.vue'
import PostList from '@/components/posts/PostList.vue'
import { t } from '@/i18n.js'

function mediaKinds() {
  return {
    pictures: {
      flag: 'pictures',
      label: t('profile.posts'),
      icon: 'picture',
      query: '?images=1',
      emptyText: t('profile.noPosts'),
    },
    clips: {
      flag: 'reels',
      label: t('profile.reels'),
      icon: 'clapperboard-play',
      query: '?videos=1',
      emptyText: t('profile.noReels'),
    },
  }
}

function activityKinds() {
  return {
    feeds: {
      label: t('profile.posts'),
      icon: 'list-timeline',
      query: 'activities/',
      emptyText: t('profile.noPosts'),
    },
    comments: {
      label: t('profile.comments'),
      icon: 'comments',
      query: 'activities/?comments=1',
      emptyText: t('profile.noComments'),
    },
  }
}

function toOptions(entries) {
  return map(entries, ({ label, icon }, value) => ({ value, label, icon }))
}

export default {
  name: 'ProfilePosts',
  components: { BaseSwitcher, PostList },
  props: {
    profile: { type: Object, required: true },
    timeline: { type: Boolean, required: true },
  },
  computed: {
    availableMedia() {
      return Object.keys(mediaKinds()).filter((key) => this.profile.media?.[mediaKinds()[key].flag])
    },
    media() {
      const requested = this.$route.query.media
      if (this.availableMedia.includes(requested)) return requested
      return this.availableMedia[0] ?? 'pictures'
    },
    activity() {
      const requested = this.$route.query.activity
      return Object.hasOwn(activityKinds(), requested) ? requested : 'feeds'
    },
    switcher() {
      if (this.timeline) {
        return { param: 'activity', options: toOptions(activityKinds()), active: this.activity }
      }
      if (this.availableMedia.length > 1) {
        return { param: 'media', options: toOptions(mediaKinds()), active: this.media }
      }
      return null
    },
    kind() {
      return this.timeline ? activityKinds()[this.activity] : mediaKinds()[this.media]
    },
    url() {
      return `${postsApi.userPostsUrl(this.profile.username)}${this.kind.query}`
    },
  },
}
</script>

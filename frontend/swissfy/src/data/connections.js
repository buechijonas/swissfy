import { t } from '@/i18n.js'

export function connections() {
  return {
    followers: { title: t('connections.followers'), emptyText: t('connections.noFollowers') },
    following: { title: t('connections.following'), emptyText: t('connections.noFollowing') },
    friends: { title: t('connections.friends'), emptyText: t('connections.noFriends') },
  }
}

export function connectionTitle(route) {
  return `@${route.params.username} ${connections()[route.params.connection].title}`
}

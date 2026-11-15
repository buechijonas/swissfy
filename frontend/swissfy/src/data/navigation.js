import { useChatsStore } from '@/stores/chats.js'
import { useNotificationsStore } from '@/stores/notifications.js'
import { t } from '@/i18n.js'

export const docsUrl = import.meta.env.VITE_DOCS_URL ?? 'https://docs.swissfy.ch'

export function isPermitted(item, authStore) {
  return !item.permission || Boolean(authStore.user?.permissions[item.permission])
}

export function canAccess(item, authStore) {
  if (item.requiresAuth && !authStore.isAuthenticated) return false
  return isPermitted(item, authStore)
}

export function isListed(item, authStore) {
  if (item.hiddenForGuests && !authStore.isAuthenticated) return false
  return isPermitted(item, authStore)
}

export function isLocked(item, authStore) {
  return !canAccess(item, authStore)
}

export function navigationItems() {
  return [
    { key: 'dashboard', label: t('navigation.home'), icon: 'house-blank', to: '/', footer: true },
    {
      key: 'reels',
      label: t('navigation.reels'),
      icon: 'clapperboard-play',
      to: '/reels',
      requiresAuth: true,
      footer: true,
    },
    {
      key: 'search',
      label: t('navigation.search'),
      icon: 'search',
      to: '/search',
      requiresAuth: true,
      footer: true,
    },
    {
      key: 'notifications',
      label: t('navigation.notifications'),
      icon: 'bell',
      to: '/notifications',
      requiresAuth: true,
      desktopOnly: true,
      badge: () => useNotificationsStore().unread,
    },
    {
      key: 'chats',
      label: t('navigation.chats'),
      icon: 'comments',
      to: '/chats',
      requiresAuth: true,
      footer: true,
      badge: () => useChatsStore().unread.length,
    },
    {
      key: 'profile',
      label: t('navigation.profile'),
      avatar: true,
      to: '/profile',
      requiresAuth: true,
      hiddenForGuests: true,
      footer: true,
    },
    {
      key: 'moderation',
      label: t('navigation.moderation'),
      icon: 'shield-exclamation',
      to: '/moderation',
      divider: true,
      requiresAuth: true,
      permission: 'moderate',
    },
    {
      key: 'administration',
      label: t('navigation.administration'),
      icon: 'tie',
      to: '/administration',
      requiresAuth: true,
      permission: 'administrate',
    },
  ]
}

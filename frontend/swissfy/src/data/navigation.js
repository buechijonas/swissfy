import { useChatsStore } from '@/stores/chats.js'
import { useNotificationsStore } from '@/stores/notifications.js'

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

export const navigationItems = [
  { key: 'dashboard', label: 'Startseite', icon: 'house-blank', to: '/', footer: true },
  {
    key: 'reels',
    label: 'Seeds',
    icon: 'clapperboard-play',
    to: '/reels',
    requiresAuth: true,
    footer: true,
  },
  {
    key: 'search',
    label: 'Suchen',
    icon: 'search',
    to: '/search',
    requiresAuth: true,
    footer: true,
  },
  {
    key: 'notifications',
    label: 'Benachrichtigungen',
    icon: 'bell',
    to: '/notifications',
    requiresAuth: true,
    desktopOnly: true,
    badge: () => useNotificationsStore().unread,
  },
  {
    key: 'chats',
    label: 'Chats',
    icon: 'comments',
    to: '/chats',
    requiresAuth: true,
    footer: true,
    badge: () => useChatsStore().unread.length,
  },
  {
    key: 'profile',
    label: 'Profil',
    avatar: true,
    to: '/profile',
    requiresAuth: true,
    hiddenForGuests: true,
    footer: true,
  },
  {
    key: 'moderation',
    label: 'Moderation',
    icon: 'shield-exclamation',
    to: '/moderation',
    divider: true,
    requiresAuth: true,
    permission: 'moderate',
  },
  {
    key: 'administration',
    label: 'Administration',
    icon: 'tie',
    to: '/administration',
    requiresAuth: true,
    permission: 'administrate',
  },
]

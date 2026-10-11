import { useChatsStore } from '@/stores/chats.js'
import { useNotificationsStore } from '@/stores/notifications.js'

export const MODERATION_ROLES = ['moderator', 'admin']
export const ADMINISTRATION_ROLES = ['admin']

export function canAccess(item, authStore) {
  if (item.requiresAuth && !authStore.isAuthenticated) return false
  return !item.roles || item.roles.includes(authStore.user?.role)
}

export const navigationItems = [
  { key: 'dashboard', label: 'Startseite', icon: 'house-blank', to: '/', footer: true },
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
    badge: () => useChatsStore().unread.length,
  },
  { key: 'saved', label: 'Gespeichert', icon: 'bookmark', to: '/saved', requiresAuth: true },
  {
    key: 'profile',
    label: 'Profil',
    avatar: true,
    to: '/profile',
    requiresAuth: true,
    footer: true,
  },
  {
    key: 'moderation',
    label: 'Moderation',
    icon: 'shield-exclamation',
    to: '/moderation',
    divider: true,
    requiresAuth: true,
    roles: MODERATION_ROLES,
  },
  {
    key: 'administration',
    label: 'Administration',
    icon: 'tie',
    to: '/administration',
    requiresAuth: true,
    roles: ADMINISTRATION_ROLES,
  },
  {
    key: 'settings',
    label: 'Einstellungen',
    icon: 'settings',
    to: '/settings',
    mobileOnly: true,
  },
]

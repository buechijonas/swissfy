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
  { key: 'chats', label: 'Chats', icon: 'comments', to: '/chats', requiresAuth: true },
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
    key: 'settings',
    label: 'Einstellungen',
    icon: 'settings',
    to: '/settings',
    mobileOnly: true,
  },
]

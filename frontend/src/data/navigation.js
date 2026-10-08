export const navigationItems = [
  { key: 'dashboard', label: 'Startseite', icon: 'house-blank', to: '/' },
  { key: 'search', label: 'Suchen', icon: 'search', to: '/search', requiresAuth: true },
  { key: 'chats', label: 'Chats', icon: 'comments', to: '/chats', requiresAuth: true },
  { key: 'saved', label: 'Gespeichert', icon: 'bookmark', to: '/saved', requiresAuth: true },
  { key: 'profile', label: 'Profil', avatar: true, to: '/profile', requiresAuth: true },
]

import { createRouter, createWebHistory } from 'vue-router'
import { useTitle } from '@vueuse/core'

import { useAuthStore } from '@/stores/auth.js'
import { canAccess } from '@/data/navigation.js'
import { connectionTitle } from '@/data/connections.js'
import { pageTitle } from '@/lib/title.js'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),

  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/HomeView.vue'),
      meta: { title: 'Startseite', activeNavigation: 'dashboard' },
    },
    {
      path: '/reels',
      name: 'reels',
      component: () => import('@/views/ReelsView.vue'),
      meta: { title: 'Seeds', activeNavigation: 'reels', requiresAuth: true },
    },
    {
      path: '/search',
      name: 'search',
      component: () => import('@/views/SearchView.vue'),
      meta: { title: 'Suchen', activeNavigation: 'search', requiresAuth: true },
    },
    {
      path: '/chats',
      name: 'chats',
      component: () => import('@/views/ChatsView.vue'),
      meta: { title: 'Chats', activeNavigation: 'chats', requiresAuth: true },
    },
    {
      path: '/chats/:username',
      name: 'chat',
      component: () => import('@/views/ChatView.vue'),
      meta: { title: 'Chat', activeNavigation: 'chats', requiresAuth: true },
    },
    {
      path: '/posts/:id([0-9a-f-]{36})',
      name: 'post',
      component: () => import('@/views/PostView.vue'),
      meta: { title: 'Feed', requiresAuth: true },
    },
    {
      path: '/comments/:id([0-9a-f-]{36})',
      name: 'comment',
      component: () => import('@/views/CommentView.vue'),
      meta: { title: 'Kommentar', requiresAuth: true },
    },
    {
      path: '/notifications',
      name: 'notifications',
      component: () => import('@/views/NotificationsView.vue'),
      meta: {
        title: 'Benachrichtigungen',
        activeNavigation: 'notifications',
        requiresAuth: true,
      },
    },
    {
      path: '/moderation',
      name: 'moderation',
      component: () => import('@/views/ModerationView.vue'),
      meta: {
        title: 'Moderation',
        activeNavigation: 'moderation',
        requiresAuth: true,
        permission: 'moderate',
      },
    },
    {
      path: '/moderation/posts/:id([0-9a-f-]{36})',
      name: 'moderation-post',
      component: () => import('@/views/PostView.vue'),
      props: { moderation: true },
      meta: {
        title: 'Moderation',
        activeNavigation: 'moderation',
        requiresAuth: true,
        permission: 'moderate',
      },
    },
    {
      path: '/moderation/comments/:id([0-9a-f-]{36})',
      name: 'moderation-comment',
      component: () => import('@/views/CommentView.vue'),
      props: { moderation: true },
      meta: {
        title: 'Moderation',
        activeNavigation: 'moderation',
        requiresAuth: true,
        permission: 'moderate',
      },
    },
    {
      path: '/administration',
      name: 'administration',
      component: () => import('@/views/AdministrationView.vue'),
      meta: {
        title: 'Administration',
        activeNavigation: 'administration',
        requiresAuth: true,
        permission: 'administrate',
      },
    },
    {
      path: '/saved',
      name: 'saved',
      component: () => import('@/views/SavedView.vue'),
      meta: { title: 'Gespeichert', activeNavigation: 'saved', requiresAuth: true },
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('@/views/ProfileView.vue'),
      meta: { title: 'Profil', activeNavigation: 'profile', requiresAuth: true },
    },
    {
      path: '/profile/:username',
      name: 'user-profile',
      component: () => import('@/views/ProfileView.vue'),
      meta: { title: 'Profil', requiresAuth: true },
    },
    {
      path: '/profile/:username/:connection(followers|following|friends)',
      name: 'user-connections',
      component: () => import('@/views/ConnectionsView.vue'),
      meta: { title: connectionTitle, requiresAuth: true },
    },
    {
      path: '/profile/:username/albums/:id([0-9a-f-]{36})',
      name: 'user-album',
      component: () => import('@/views/AlbumView.vue'),
      meta: { title: 'Album', requiresAuth: true },
    },
    {
      path: '/profile/:username/reels/:id([0-9a-f-]{36})',
      name: 'user-reels',
      component: () => import('@/views/ReelsView.vue'),
      meta: { title: 'Seeds', requiresAuth: true },
    },
    {
      path: '/upload/:kind(feed|story)',
      name: 'upload',
      component: () => import('@/views/UploadView.vue'),
      meta: {
        title: (route) => (route.params.kind === 'story' ? 'Neue Story' : 'Neuer Feed'),
        requiresAuth: true,
      },
    },
    {
      path: '/hashtags/:name',
      name: 'hashtag',
      component: () => import('@/views/HashtagView.vue'),
      meta: { title: 'Hashtag', activeNavigation: 'search', requiresAuth: true },
    },
    {
      path: '/hashtags/:name/reels/:id([0-9a-f-]{36})',
      name: 'hashtag-reels',
      component: () => import('@/views/ReelsView.vue'),
      meta: { title: 'Seeds', requiresAuth: true },
    },
    {
      path: '/impressum',
      name: 'impressum',
      component: () => import('@/views/legal/ImpressumView.vue'),
      meta: { title: 'Impressum' },
    },
    {
      path: '/privacy',
      name: 'privacy',
      component: () => import('@/views/legal/PrivacyView.vue'),
      meta: { title: 'Datenschutzerklärung' },
    },
    {
      path: '/terms',
      name: 'terms',
      component: () => import('@/views/legal/TermsView.vue'),
      meta: { title: 'Nutzungsrichtlinien' },
    },
    {
      path: '/disclaimer',
      name: 'disclaimer',
      component: () => import('@/views/legal/DisclaimerView.vue'),
      meta: { title: 'Haftungsausschluss' },
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/auth/LoginView.vue'),
      meta: { title: 'Anmelden' },
    },
    {
      path: '/logout',
      name: 'logout',
      component: () => import('@/views/auth/LogoutView.vue'),
      meta: { title: 'Abmelden' },
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('@/views/SettingsView.vue'),
      meta: { title: 'Einstellungen', activeNavigation: 'settings' },
    },
  ],
})

const CONSENT_GATES = [
  { field: 'privacy', path: '/privacy' },
  { field: 'terms', path: '/terms' },
  { field: 'disclaimer', path: '/disclaimer' },
]

router.beforeEach((to) => {
  const authStore = useAuthStore()
  if (!authStore.ready) {
    return true
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return '/login'
  }

  if (!canAccess(to.meta, authStore)) {
    return '/'
  }

  if (!authStore.isAuthenticated || to.name === 'logout') {
    return true
  }

  const consent = authStore.user.consent
  for (const gate of CONSENT_GATES) {
    if (!consent[gate.field]) {
      return to.path === gate.path ? true : gate.path
    }
  }

  return true
})

const documentTitle = useTitle()

router.afterEach((to) => {
  const title = pageTitle(to)
  documentTitle.value = title ? `${title} – Swissfy` : 'Swissfy'
})

export default router

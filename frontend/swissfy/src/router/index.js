import { createRouter, createWebHistory } from 'vue-router'
import { useTitle } from '@vueuse/core'

import { useAuthStore } from '@/stores/auth.js'
import { canAccess } from '@/data/navigation.js'
import { connectionTitle } from '@/data/connections.js'
import { pageTitle } from '@/lib/title.js'
import { watch } from 'vue'
import { legalTitle } from '@core/legal/index.js'
import { language } from '@core/lib/language.js'
import { t } from '@/i18n.js'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),

  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/HomeView.vue'),
      meta: { title: () => t('routes.home'), activeNavigation: 'dashboard' },
    },
    {
      path: '/reels',
      name: 'reels',
      component: () => import('@/views/ReelsView.vue'),
      meta: { title: () => t('routes.reels'), activeNavigation: 'reels', requiresAuth: true },
    },
    {
      path: '/search',
      name: 'search',
      component: () => import('@/views/SearchView.vue'),
      meta: { title: () => t('routes.search'), activeNavigation: 'search', requiresAuth: true },
    },
    {
      path: '/chats',
      name: 'chats',
      component: () => import('@/views/ChatsView.vue'),
      meta: { title: () => t('routes.chats'), activeNavigation: 'chats', requiresAuth: true },
    },
    {
      path: '/chats/:username',
      name: 'chat',
      component: () => import('@/views/ChatView.vue'),
      meta: { title: () => t('routes.chat'), activeNavigation: 'chats', requiresAuth: true },
    },
    {
      path: '/posts/:id([0-9a-f-]{36})',
      name: 'post',
      component: () => import('@/views/PostView.vue'),
      meta: { title: () => t('routes.post'), requiresAuth: true },
    },
    {
      path: '/comments/:id([0-9a-f-]{36})',
      name: 'comment',
      component: () => import('@/views/CommentView.vue'),
      meta: { title: () => t('routes.comment'), requiresAuth: true },
    },
    {
      path: '/notifications',
      name: 'notifications',
      component: () => import('@/views/NotificationsView.vue'),
      meta: {
        title: () => t('routes.notifications'),
        activeNavigation: 'notifications',
        requiresAuth: true,
      },
    },
    {
      path: '/moderation',
      name: 'moderation',
      component: () => import('@/views/ModerationView.vue'),
      meta: {
        title: () => t('routes.moderation'),
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
        title: () => t('routes.moderation'),
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
        title: () => t('routes.moderation'),
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
        title: () => t('routes.administration'),
        activeNavigation: 'administration',
        requiresAuth: true,
        permission: 'administrate',
      },
    },
    {
      path: '/saved',
      name: 'saved',
      component: () => import('@/views/SavedView.vue'),
      meta: { title: () => t('routes.saved'), activeNavigation: 'saved', requiresAuth: true },
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('@/views/ProfileView.vue'),
      meta: { title: () => t('routes.profile'), activeNavigation: 'profile', requiresAuth: true },
    },
    {
      path: '/profile/:username',
      name: 'user-profile',
      component: () => import('@/views/ProfileView.vue'),
      meta: { title: () => t('routes.profile'), requiresAuth: true },
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
      meta: { title: () => t('routes.album'), requiresAuth: true },
    },
    {
      path: '/profile/:username/reels/:id([0-9a-f-]{36})',
      name: 'user-reels',
      component: () => import('@/views/ReelsView.vue'),
      meta: { title: () => t('routes.reels'), requiresAuth: true },
    },
    {
      path: '/upload/:kind(feed|story)',
      name: 'upload',
      component: () => import('@/views/UploadView.vue'),
      meta: {
        title: (route) =>
          route.params.kind === 'story' ? t('routes.newStory') : t('routes.newPost'),
        requiresAuth: true,
      },
    },
    {
      path: '/hashtags/:name',
      name: 'hashtag',
      component: () => import('@/views/HashtagView.vue'),
      meta: { title: () => t('routes.hashtag'), activeNavigation: 'search', requiresAuth: true },
    },
    {
      path: '/hashtags/:name/reels/:id([0-9a-f-]{36})',
      name: 'hashtag-reels',
      component: () => import('@/views/ReelsView.vue'),
      meta: { title: () => t('routes.reels'), requiresAuth: true },
    },
    {
      path: '/consent/:page(privacy|terms|disclaimer)',
      name: 'consent',
      component: () => import('@/views/ConsentView.vue'),
      meta: { title: (route) => legalTitle(route.params.page), requiresAuth: true },
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/auth/LoginView.vue'),
      meta: { title: () => t('routes.login') },
    },
    {
      path: '/logout',
      name: 'logout',
      component: () => import('@/views/auth/LogoutView.vue'),
      meta: { title: () => t('routes.logout') },
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('@/views/SettingsView.vue'),
      meta: { title: () => t('routes.settings'), activeNavigation: 'settings' },
    },
  ],
})

const CONSENT_GATES = [
  { field: 'privacy', path: '/consent/privacy' },
  { field: 'terms', path: '/consent/terms' },
  { field: 'disclaimer', path: '/consent/disclaimer' },
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

function updateTitle(route) {
  const title = pageTitle(route)
  documentTitle.value = title ? `${title} – Swissfy` : 'Swissfy'
}

router.afterEach(updateTitle)
watch(language, () => updateTitle(router.currentRoute.value))

export default router

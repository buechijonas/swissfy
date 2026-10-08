import { createRouter, createWebHistory } from 'vue-router'

import { useAuthStore } from '@/stores/auth.js'
import HomeView from '@/views/HomeView.vue'
import SettingsView from '@/views/SettingsView.vue'
import SearchView from '@/views/SearchView.vue'
import ChatsView from '@/views/ChatsView.vue'
import ChatView from '@/views/ChatView.vue'
import SavedView from '@/views/SavedView.vue'
import ProfileView from '@/views/ProfileView.vue'
import ImpressumView from '@/views/legal/ImpressumView.vue'
import PrivacyView from '@/views/legal/PrivacyView.vue'
import TermsView from '@/views/legal/TermsView.vue'
import DisclaimerView from '@/views/legal/DisclaimerView.vue'
import LoginView from '@/views/auth/LoginView.vue'
import LogoutView from '@/views/auth/LogoutView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),

  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
      meta: { title: 'Startseite', activeNavigation: 'dashboard' },
    },
    {
      path: '/search',
      name: 'search',
      component: SearchView,
      meta: { title: 'Suchen', activeNavigation: 'search', requiresAuth: true },
    },
    {
      path: '/chats',
      name: 'chats',
      component: ChatsView,
      meta: { title: 'Chats', activeNavigation: 'chats', requiresAuth: true },
    },
    {
      path: '/chats/:username',
      name: 'chat',
      component: ChatView,
      meta: { title: 'Chat', activeNavigation: 'chats', requiresAuth: true },
    },
    {
      path: '/saved',
      name: 'saved',
      component: SavedView,
      meta: { title: 'Gespeichert', activeNavigation: 'saved', requiresAuth: true },
    },
    {
      path: '/profile',
      name: 'profile',
      component: ProfileView,
      meta: { title: 'Profil', activeNavigation: 'profile', requiresAuth: true },
    },
    {
      path: '/profile/:username',
      name: 'user-profile',
      component: ProfileView,
      meta: { title: 'Profil', requiresAuth: true },
    },
    {
      path: '/impressum',
      name: 'impressum',
      component: ImpressumView,
      meta: { title: 'Impressum' },
    },
    {
      path: '/privacy',
      name: 'privacy',
      component: PrivacyView,
      meta: { title: 'Datenschutzerklärung' },
    },
    {
      path: '/terms',
      name: 'terms',
      component: TermsView,
      meta: { title: 'Nutzungsrichtlinien' },
    },
    {
      path: '/disclaimer',
      name: 'disclaimer',
      component: DisclaimerView,
      meta: { title: 'Haftungsausschluss' },
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { title: 'Anmelden' },
    },
    {
      path: '/logout',
      name: 'logout',
      component: LogoutView,
      meta: { title: 'Abmelden' },
    },
    {
      path: '/settings',
      name: 'settings',
      component: SettingsView,
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

router.afterEach((to) => {
  const title = to.meta.title
  document.title = title ? `${title} – Swissfy` : 'Swissfy'
})

export default router

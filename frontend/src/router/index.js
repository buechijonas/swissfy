import { createRouter, createWebHistory } from 'vue-router'

import { useAuthStore } from '@/stores/auth.js'
import HomeView from '@/views/HomeView.vue'
import SettingsView from '@/views/SettingsView.vue'
import SearchView from '@/views/SearchView.vue'
import ChatsView from '@/views/ChatsView.vue'
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
      meta: { activeNavigation: 'dashboard' },
    },
    {
      path: '/search',
      name: 'search',
      component: SearchView,
      meta: { activeNavigation: 'search', requiresAuth: true },
    },
    {
      path: '/chats',
      name: 'chats',
      component: ChatsView,
      meta: { activeNavigation: 'chats', requiresAuth: true },
    },
    {
      path: '/saved',
      name: 'saved',
      component: SavedView,
      meta: { activeNavigation: 'saved', requiresAuth: true },
    },
    {
      path: '/profile',
      name: 'profile',
      component: ProfileView,
      meta: { activeNavigation: 'profile', requiresAuth: true },
    },
    {
      path: '/profile/:username',
      name: 'user-profile',
      component: ProfileView,
      meta: { requiresAuth: true },
    },
    {
      path: '/impressum',
      name: 'impressum',
      component: ImpressumView,
    },
    {
      path: '/privacy',
      name: 'privacy',
      component: PrivacyView,
    },
    {
      path: '/terms',
      name: 'terms',
      component: TermsView,
    },
    {
      path: '/disclaimer',
      name: 'disclaimer',
      component: DisclaimerView,
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
    },
    {
      path: '/logout',
      name: 'logout',
      component: LogoutView,
    },
    {
      path: '/settings',
      name: 'settings',
      component: SettingsView,
    },
  ],
})

const PAGE_TITLES = {
  home: 'Startseite',
  search: 'Suchen',
  chats: 'Chats',
  saved: 'Gespeichert',
  profile: 'Profil',
  'user-profile': 'Profil',
  impressum: 'Impressum',
  privacy: 'Datenschutzerklärung',
  terms: 'Nutzungsrichtlinien',
  disclaimer: 'Haftungsausschluss',
  login: 'Anmelden',
  logout: 'Abmelden',
  settings: 'Einstellungen',
}

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
  const title = PAGE_TITLES[to.name]
  document.title = title ? `${title} – Swissfy` : 'Swissfy'
})

export default router

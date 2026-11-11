import { createRouter, createWebHistory } from 'vue-router'

import ChangelogsView from '@/views/ChangelogsView.vue'
import ChangelogView from '@/views/ChangelogView.vue'
import SettingsView from '@/views/SettingsView.vue'

const PAGE_TITLES = {
  changelogs: 'Changelog',
  settings: 'Einstellungen',
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior: () => ({ top: 0 }),

  routes: [
    {
      path: '/',
      name: 'changelogs',
      component: ChangelogsView,
      meta: { activeNavigation: 'changelogs' },
    },
    {
      path: '/changelog/:version',
      name: 'changelog',
      component: ChangelogView,
      meta: { activeNavigation: 'changelogs' },
    },
    {
      path: '/settings',
      name: 'settings',
      component: SettingsView,
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

router.afterEach((to) => {
  const title = to.name === 'changelog' ? `v${to.params.version}` : PAGE_TITLES[to.name]
  document.title = title ? `${title} – Swissfy Docs` : 'Swissfy Docs'
})

export default router

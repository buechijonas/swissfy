import { watch } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import { LEGAL_PAGES, legalTitle } from '@core/legal/index.js'
import { language } from '@core/lib/language.js'

import ChangelogsView from '@/views/ChangelogsView.vue'
import ChangelogView from '@/views/ChangelogView.vue'
import SettingsView from '@/views/SettingsView.vue'
import LegalView from '@/views/LegalView.vue'
import { t } from '@/i18n.js'

function pageTitles() {
  return {
    changelogs: t('navigation.changelog'),
    settings: t('navigation.settings'),
    ...Object.fromEntries(LEGAL_PAGES.map((page) => [page, legalTitle(page)])),
  }
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
    ...LEGAL_PAGES.map((page) => ({
      path: `/${page}`,
      name: page,
      component: LegalView,
      meta: { activeNavigation: page },
    })),
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

function updateTitle(to) {
  const title = to.name === 'changelog' ? `v${to.params.version}` : pageTitles()[to.name]
  document.title = title ? `${title} – Swissfy Docs` : 'Swissfy Docs'
}

router.afterEach(updateTitle)
watch(language, () => updateTitle(router.currentRoute.value))

export default router

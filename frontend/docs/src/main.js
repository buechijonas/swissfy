import '@fontsource/manrope/700.css'
import './assets/main.css'
import '@core/lib/appearance.js'

import { createPinia } from 'pinia'
import { createApp } from 'vue'
import packageJson from '../package.json'
import App from './App.vue'
import { iconSource } from './assets/icons.js'
import { navigationItems } from './data/navigation.js'
import { i18n, i18nReady } from './i18n.js'
import router from './router'

const app = createApp(App)

app.use(createPinia())
app.use(i18n)
app.use(router)
app.provide('iconSource', iconSource)
app.provide('app', {
  title: 'Swissfy',
  version: packageJson.version,
  navigationItems,
  appSwitches: [
    { label: 'Swissfy', url: import.meta.env.VITE_SWISSFY_URL ?? 'https://swissfy.ch' },
  ],
})

i18nReady().then(() => app.mount('#app'))

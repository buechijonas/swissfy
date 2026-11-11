import '@fontsource/manrope/700.css'
import './assets/main.css'
import '@core/lib/appearance.js'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { navigationItems } from './data/navigation.js'
import packageJson from '../package.json'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.provide('app', {
  title: 'Swissfy',
  version: packageJson.version,
  navigationItems,
  appSwitches: [
    { label: 'Swissfy', url: import.meta.env.VITE_SWISSFY_URL ?? 'https://swissfy.ch' },
  ],
})

app.mount('#app')

import '@fontsource-variable/fraunces'
import '@fontsource-variable/nunito'
import '@fontsource-variable/cormorant-garamond'
import '@fontsource-variable/lora'
import './assets/main.css'
import './lib/preferences.js'

import { createPinia } from 'pinia'
import { createApp } from 'vue'
import App from './App.vue'
import { iconSource } from './assets/icons.js'
import { i18n, i18nReady } from './i18n.js'
import router from './router'

const app = createApp(App)

app.use(createPinia())
app.use(i18n)
app.use(router)
app.provide('iconSource', iconSource)

i18nReady().then(() => app.mount('#app'))

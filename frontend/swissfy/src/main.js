import '@fontsource-variable/fraunces'
import '@fontsource-variable/nunito'
import '@fontsource-variable/cormorant-garamond'
import '@fontsource-variable/lora'
import './assets/main.css'
import './lib/preferences.js'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import { iconSource } from './assets/icons.js'
import router from './router'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.provide('iconSource', iconSource)

app.mount('#app')

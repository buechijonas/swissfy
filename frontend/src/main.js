import './assets/main.css'
import './lib/theme.js'
import './lib/dyslexia.js'
import './lib/contrast.js'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')

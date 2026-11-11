import { fileURLToPath, URL } from 'node:url'

import { defineConfig, searchForWorkspaceRoot } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

const core = fileURLToPath(new URL('../core/src', import.meta.url))

export default defineConfig({
  plugins: [vue(), tailwindcss()],

  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      '@core': core,
    },
    dedupe: ['vue', 'vue-router', 'pinia'],
  },

  server: {
    host: '0.0.0.0',
    port: 5176,
    strictPort: true,

    fs: {
      allow: [searchForWorkspaceRoot(fileURLToPath(new URL('.', import.meta.url))), core],
    },

    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
    },
  },
})

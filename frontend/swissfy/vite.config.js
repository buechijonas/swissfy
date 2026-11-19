import { fileURLToPath, URL } from 'node:url'
import tailwindcss from '@tailwindcss/vite'
import vue from '@vitejs/plugin-vue'
import { defineConfig, searchForWorkspaceRoot } from 'vite'

const core = fileURLToPath(new URL('../core/src', import.meta.url))

export default defineConfig({
  plugins: [vue(), tailwindcss()],

  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      '@core': core,
    },
    dedupe: ['vue', 'vue-router', 'pinia', 'vue-i18n'],
  },

  test: {
    environment: 'jsdom',
    setupFiles: ['./tests/setup.js'],
  },

  server: {
    host: '0.0.0.0',
    port: 5175,
    strictPort: true,

    fs: {
      allow: [searchForWorkspaceRoot(fileURLToPath(new URL('.', import.meta.url))), core],
    },

    proxy: {
      '/api/events': {
        target: 'http://events:8000',
        changeOrigin: true,
      },
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
    },
  },
})

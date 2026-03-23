import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],

  resolve: {
    alias: {
      // '@' maps to the src/ directory, so imports like '@/stores/app' work everywhere
      '@': resolve(__dirname, 'src'),
    },
  },

  server: {
    port: 5173,
    proxy: {
      // Forward /api/* to Django backend — mirrors the production Nginx setup.
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // Forward /admin/* to Django so the admin login page and session cookie
      // are served under the same origin (localhost:5173) as the Vue SPA.
      // Without this, Django sets the sessionid cookie on :8000 but the SPA
      // runs on :5173, so the cookie is never sent with subsequent /api/ calls.
      '/admin': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // Forward /i18n/* (set_language) and /static/* (admin CSS/JS assets)
      // so the Django admin UI renders correctly through the Vite proxy.
      '/i18n': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/static': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },

  build: {
    outDir: 'dist',
    sourcemap: true,
  },
})

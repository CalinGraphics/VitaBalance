import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        // Bibliotecile grele stau în chunk-uri proprii, ca prima pictare să nu le aștepte.
        manualChunks: {
          charts: ['recharts'],
          motion: ['framer-motion'],
          i18n: ['i18next', 'react-i18next'],
        },
      },
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // Aliniat cu timeout-ul lung pentru POST /recommendations (regenerare)
        timeout: 130_000,
      },
    },
  },
})

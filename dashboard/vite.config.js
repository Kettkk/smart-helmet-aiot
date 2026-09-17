import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  build: {
    chunkSizeWarningLimit: 650,
  },
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8080',
      '/actuator': 'http://localhost:8080',
    },
  },
})

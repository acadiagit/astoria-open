// Filename: console/vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // FIX: Changed target port from 8000 to the backend port 7860
      '/api': {
        target: 'http://127.0.0.1:7860', 
        changeOrigin: true,
      },
    },
  },
})

// -- end of file --// -- end of file --

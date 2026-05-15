import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/requirements': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/approvals': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/workflow': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/registry': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/workflow-config': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/workbench': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/events': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/lifecycle': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})

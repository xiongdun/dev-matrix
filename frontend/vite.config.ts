import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

/**
 * API 路径前缀列表
 * 这些路径的请求会被代理到后端，不会 fallback 到 index.html
 */
const API_PREFIXES = [
  '/requirements',
  '/approvals',
  '/health',
  '/registry',
  '/events',
  '/lifecycle',
  '/api',
  '/workflow-config',
  '/workflow-instances',
]

/**
 * Vite 内部路径前缀，不应该被 fallback
 */
const VITE_INTERNAL_PREFIXES = [
  '/@vite',
  '/@id',
  '/@fs',
  '/__vite',
  '/src/',
  '/node_modules',
  '/assets/',
]

function isApiRequest(url: string): boolean {
  return API_PREFIXES.some(prefix => url.startsWith(prefix))
}

function isViteInternal(url: string): boolean {
  return VITE_INTERNAL_PREFIXES.some(prefix => url.startsWith(prefix))
}

function isStaticAsset(url: string): boolean {
  return url.includes('.') && !url.startsWith('/@')
}

export default defineConfig({
  plugins: [
    vue(),
    {
      name: 'spa-fallback',
      configureServer(server) {
        server.middlewares.use((req, res, next) => {
          const url = req.url || ''
          if (req.method !== 'GET') return next()
          if (isApiRequest(url)) return next()
          if (isViteInternal(url)) return next()
          if (isStaticAsset(url)) return next()
          req.url = '/index.html'
          next()
        })
      },
    },
  ],
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
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/registry': {
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
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/workflow-config': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/workflow-instances': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
  },
})

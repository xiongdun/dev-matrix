import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { readFileSync } from 'fs'
import { resolve } from 'path'

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
          // API 请求继续走到 proxy
          if (url.startsWith('/api/') || url === '/health') return next()
          if (isViteInternal(url)) return next()
          if (isStaticAsset(url)) return next()

          // 前端路由页面：直接返回 index.html 内容
          try {
            const indexPath = resolve(__dirname, 'index.html')
            const html = readFileSync(indexPath, 'utf-8')
            res.setHeader('Content-Type', 'text/html')
            res.statusCode = 200
            res.end(html)
          } catch {
            next()
          }
        })
      },
    },
  ],
  server: {
    port: 3000,
    watch: {
      // NTFS 挂载下 .venv/node_modules 变更会触发无效 HMR，排除它们
      ignored: ['**/.venv/**', '**/node_modules/**', '**/.git/**', '**/dist/**'],
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/health': {
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

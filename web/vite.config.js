import { fileURLToPath, URL } from 'node:url'
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      }
    },
    server: {
      proxy: {
        '^/api': {
          // 开发默认走本地 api 容器，线上可通过 VITE_API_URL 覆盖
          target: env.VITE_API_URL || 'http://127.0.0.1:5050',
          changeOrigin: true
        },
        '^/crawler-api': {
          // 开发环境直连爬虫服务（生产环境由 nginx 处理 /crawler-api 反代）
          target: env.VITE_CRAWLER_URL || 'http://127.0.0.1:18060',
          changeOrigin: true,
          rewrite: path => path.replace(/^\/crawler-api/, '/api/v1')
        }
      },
      watch: {
        usePolling: true,
        ignored: ['**/node_modules/**', '**/dist/**']
      },
      host: '0.0.0.0'
    }
  }
})


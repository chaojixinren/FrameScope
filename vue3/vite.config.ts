import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    proxy: {
      // 代理静态文件请求到后端服务器
      // 将 /static 路径的请求代理到后端服务器（默认端口8483）
      '/static': {
        target: 'http://localhost:8483',
        changeOrigin: true,
        secure: false
      }
    }
  }
})

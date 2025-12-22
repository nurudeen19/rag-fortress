import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// Get API URLs from environment variables - no hardcoded defaults
const getApiUrls = () => {
  if (!process.env.VITE_API_URLS) {
    throw new Error('VITE_API_URLS environment variable is required. Please check your .env file.')
  }
  
  // Parse comma-separated URLs and clean them
  const urls = process.env.VITE_API_URLS.split(',')
    .map(url => url.trim())
    .filter(url => url)
  
  if (urls.length === 0) {
    throw new Error('VITE_API_URLS environment variable cannot be empty.')
  }
  
  return urls.join(' ')
}

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    {
      name: 'inject-csp',
      transformIndexHtml(html) {
        const apiUrls = getApiUrls()
        return html.replace('__API_URLS__', apiUrls)
      }
    }
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: process.env.VITE_API_BASE_URL || 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})

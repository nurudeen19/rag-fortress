import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// https://vitejs.dev/config/
export default defineConfig(({ command, mode }) => {
  // Load environment variables with VITE_ prefix
  const env = loadEnv(mode, process.cwd(), 'VITE_')
  
  // Get API base URL
  const apiBaseUrl = env.VITE_API_BASE_URL
  if (!apiBaseUrl) {
    throw new Error('VITE_API_BASE_URL environment variable is required. Please check your .env file.')
  }
  
  // Get API origin for CSP (just protocol + host, no path)
  const getApiOriginForCsp = () => {
    try {
      const url = new URL(apiBaseUrl)
      // Return just the origin (protocol + host) to allow all subpaths
      return `${url.protocol}//${url.host}`
    } catch (e) {
      throw new Error(`Invalid VITE_API_BASE_URL: ${apiBaseUrl}. Must be a valid URL.`)
    }
  }

  return {
    plugins: [
      vue(),
      {
        name: 'inject-csp',
        transformIndexHtml(html) {
          const apiOrigin = getApiOriginForCsp()
          return html.replace('__API_URLS__', apiOrigin)
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
          target: apiBaseUrl,
          changeOrigin: true
        }
      }
    }
  }
})

import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import compression from 'vite-plugin-compression'
import { visualizer } from 'rollup-plugin-visualizer'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, __dirname, '')
  const allowedHosts = (env.VITE_ALLOWED_HOSTS || '')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)

  return {
    plugins: [
      react(),
      compression({ algorithm: 'gzip', ext: '.gz' }),
      compression({ algorithm: 'brotliCompress', ext: '.br' }),
    ],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    build: {
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (!id.includes('node_modules')) return
            if (
              id.includes('node_modules/react/') ||
              id.includes('node_modules/react-dom/') ||
              id.includes('node_modules/scheduler/')
            )
              return 'react-vendor'
            if (id.includes('@tanstack/react-query')) return 'react-query'
            if (id.includes('lucide-react')) return 'icons'
            return 'vendor'
          },
        },
        plugins: [
          visualizer({
            filename: 'dist/stats.html',
            gzipSize: true,
            brotliSize: true,
            open: false,
          }),
        ],
      },
    },
    server: {
      host: '0.0.0.0',
      port: 5173,
      allowedHosts: allowedHosts.length > 0 ? allowedHosts : undefined,
    },
  }
})

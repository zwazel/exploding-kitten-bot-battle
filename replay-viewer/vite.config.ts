import { defineConfig } from 'vite'

// https://vitejs.dev/config/
export default defineConfig({
  // For GitHub Pages, set base to the repository name
  // When running locally, this will be ignored
  base: process.env.NODE_ENV === 'production' ? '/exploding-kitten-bot-battle/' : '/',
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
  },
})

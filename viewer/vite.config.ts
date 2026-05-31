import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  base: '/agentmemory/',
  plugins: [react()],
  build: {
    outDir: '../src/agentmemory/viewer/dist',
    emptyOutDir: true,
  },
})

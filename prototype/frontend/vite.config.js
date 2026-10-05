import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Vite dev server config. Proxy /api -> FastAPI backend (default :8000, override with API_TARGET).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: process.env.API_TARGET || 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/api/, ''),
      },
    },
  },
});

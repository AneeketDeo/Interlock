import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: 'https://rca-sentinel-864573324943.asia-south1.run.app',
        changeOrigin: true,
        secure: true,
      },
      '/health': {
        target: 'https://rca-sentinel-864573324943.asia-south1.run.app',
        changeOrigin: true,
        secure: true,
      },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});

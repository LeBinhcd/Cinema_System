import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  build: { outDir: 'dist' },
  server: { port: 5173, proxy: { '/api': 'http://127.0.0.1:5000', '/login': 'http://127.0.0.1:5000' } },
});

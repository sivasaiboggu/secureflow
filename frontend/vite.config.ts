import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

// Root-relative assets are required for direct navigation to nested SPA routes.
export default defineConfig({
  plugins: [react(), tailwindcss()],
});

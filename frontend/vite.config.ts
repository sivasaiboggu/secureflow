import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Relative asset base: the built index.html must work from any path, not
// only the server root. With the default absolute '/assets/...' paths a
// build opened from a file or served under a sub-path (GitHub Pages, a
// static host) loaded a blank page because the bundles 404'd.
export default defineConfig({
  base: './',
  plugins: [react()],
});

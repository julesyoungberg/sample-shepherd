import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [tailwindcss(), sveltekit()],
  // tauri.conf.json's devUrl expects 5173; fail instead of quietly moving to another port.
  server: { port: 5173, strictPort: true }
});

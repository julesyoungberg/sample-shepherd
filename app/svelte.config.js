import adapter from '@sveltejs/adapter-static';

// A single-page app in build/, the setup Tauri documents: one index.html serves every
// route, since the desktop shell has no server.
/** @type {import('@sveltejs/kit').Config} */
export default {
  kit: { adapter: adapter({ fallback: 'index.html' }) }
};

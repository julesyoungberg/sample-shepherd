import adapter from '@sveltejs/adapter-static';

// Plain static files in build/, ready for any static host. Nothing is deployed from here.
export default {
  kit: { adapter: adapter() }
};

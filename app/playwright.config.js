import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: 'tests',
  use: { baseURL: 'http://localhost:4173' },
  // shortcut: Chromium only, since WebKit (the plan's engine) isn't installed in cloud sessions; switch when screenshot baselines land.
  projects: [{ name: 'chromium', use: devices['Desktop Chrome'] }],
  webServer: { command: 'pnpm build && pnpm preview --port 4173 --strictPort', port: 4173, reuseExistingServer: false }
});

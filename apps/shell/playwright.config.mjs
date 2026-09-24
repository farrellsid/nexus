import { defineConfig } from '@playwright/test';

// The shell's smoke test uses the installed Microsoft Edge, like apps/web. The sandbox GPU is not
// the user's GPU: a pass here means "renders and is quiet", not "looks and performs right".
export default defineConfig({
  testDir: './tests',
  testMatch: '**/*.spec.mjs',
  timeout: 120_000,
  use: { baseURL: 'http://127.0.0.1:5175', browserName: 'chromium', channel: 'msedge' },
  webServer: {
    command: 'npm run dev -- --port 5175 --strictPort --host 127.0.0.1',
    url: 'http://127.0.0.1:5175',
    reuseExistingServer: false,
    timeout: 120_000,
  },
});

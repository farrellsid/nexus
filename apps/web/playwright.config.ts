import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  use: { baseURL: 'http://127.0.0.1:5174', browserName: 'chromium', channel: 'msedge' },
  webServer: [
    { command: '..\\..\\.venv\\Scripts\\python -m uvicorn browser_app:app --app-dir ../../backend/tests --host 127.0.0.1 --port 8001', url: 'http://127.0.0.1:8001/api/investigation', reuseExistingServer: false },
    { command: 'npm run dev -- --port 5174', url: 'http://127.0.0.1:5174', reuseExistingServer: false, env: { NEXUS_API_TARGET: 'http://127.0.0.1:8001' } },
  ],
});

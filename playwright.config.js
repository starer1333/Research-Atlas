const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './tests/e2e',
  timeout: 30000,
  retries: 0,
  workers: 1,
  reporter: 'line',
  use: {
    baseURL: process.env.ATLAS_E2E_BASE_URL || 'http://127.0.0.1:8766',
    channel: 'chrome',
    headless: true,
    viewport: { width: 1440, height: 1000 },
    trace: 'retain-on-failure'
  }
});

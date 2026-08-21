import { defineConfig, devices } from "@playwright/test";

const webPort = process.env.E2E_WEB_PORT ?? "3000";
const apiPort = process.env.E2E_API_PORT ?? "8000";
const webOrigin = `http://localhost:${webPort}`;
const apiHealthOrigin = `http://127.0.0.1:${apiPort}`;
const apiBrowserOrigin = `http://localhost:${apiPort}`;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: webOrigin,
    trace: "on-first-retry",
  },
  webServer: [
    {
      command:
        `../api/.venv/bin/python -m uvicorn app.main:app --app-dir ../api --host 127.0.0.1 --port ${apiPort}`,
      url: `${apiHealthOrigin}/api/v1/health`,
      reuseExistingServer: false,
      timeout: 120_000,
      env: {
        WEB_ORIGIN: webOrigin,
        ADMIN_USERNAME: "admin",
        ADMIN_PASSWORD_HASH:
          "$argon2id$v=19$m=65536,t=3,p=4$hT5RBO8JnzUwJE7kimaUlg$LlpRLxGRhmjhRsG+LYEZXmlaE7gmBlZi5g8nlwBtbyk",
        SESSION_SECRET: "playwright-session-secret-at-least-32-characters",
      },
    },
    {
      command: `npm run dev -- --hostname localhost --port ${webPort}`,
      url: webOrigin,
      reuseExistingServer: false,
      timeout: 120_000,
      env: {
        NEXT_PUBLIC_API_URL: `${apiBrowserOrigin}/api/v1`,
      },
    },
  ],
  projects: [
    {
      name: "chromium",
      testIgnore: /mobile/,
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "mobile",
      testMatch: /mobile.*\.spec\.ts/,
      use: { ...devices["Pixel 7"] },
    },
  ],
});

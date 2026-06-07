import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
  },
  webServer: [
    {
      command:
        "../api/.venv/bin/python -m uvicorn app.main:app --app-dir ../api --host 127.0.0.1 --port 8000",
      url: "http://127.0.0.1:8000/api/v1/health",
      reuseExistingServer: false,
      timeout: 120_000,
      env: {
        WEB_ORIGIN: "http://localhost:3000",
        ADMIN_USERNAME: "admin",
        ADMIN_PASSWORD_HASH:
          "$argon2id$v=19$m=65536,t=3,p=4$hT5RBO8JnzUwJE7kimaUlg$LlpRLxGRhmjhRsG+LYEZXmlaE7gmBlZi5g8nlwBtbyk",
        SESSION_SECRET: "playwright-session-secret-at-least-32-characters",
      },
    },
    {
      command: "npm run dev -- --hostname localhost",
      url: "http://localhost:3000",
      reuseExistingServer: false,
      timeout: 120_000,
      env: {
        NEXT_PUBLIC_API_URL: "http://localhost:8000/api/v1",
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

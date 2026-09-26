import { randomBytes } from "node:crypto";
import { defineConfig, devices } from "@playwright/test";

/**
 * End-to-end tests on the web build (N1.5). The game server runs on the committed bundle files
 * with play data in memory; sign-ins are checked against a key generated for this run only.
 */

const API_PORT = 3199;
const WEB_PORT = 8199;
export const AUTH_URL = "http://auth.e2e.test";
// Set once in the main process; the workers inherit it.
process.env.E2E_JWT_SECRET ??= randomBytes(32).toString("hex");

export default defineConfig({
  testDir: "./e2e",
  timeout: 120_000,
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: `http://localhost:${WEB_PORT}`,
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: `pnpm --filter @nidana/server exec next dev --port ${API_PORT}`,
      url: `http://localhost:${API_PORT}/api/cases`,
      reuseExistingServer: false,
      timeout: 120_000,
      env: {
        NIDANA_BUNDLE_SOURCE: "files",
        NIDANA_STORE: "memory",
        SUPABASE_URL: AUTH_URL,
        SUPABASE_JWT_SECRET: process.env.E2E_JWT_SECRET,
        NIDANA_ALLOWED_ORIGINS: `http://localhost:${WEB_PORT}`,
        NEXT_TELEMETRY_DISABLED: "1",
      },
    },
    {
      command: `npx expo export --platform web --output-dir dist --clear && npx expo serve --port ${WEB_PORT}`,
      url: `http://localhost:${WEB_PORT}`,
      reuseExistingServer: false,
      timeout: 300_000,
      env: {
        EXPO_PUBLIC_API_URL: `http://localhost:${API_PORT}`,
        EXPO_PUBLIC_SUPABASE_URL: AUTH_URL,
        // Unused: the tests place a signed session directly, so no request reaches Supabase.
        EXPO_PUBLIC_SUPABASE_KEY: randomBytes(8).toString("hex"),
        CI: "1",
      },
    },
  ],
});

export { API_PORT, WEB_PORT };

import { SignJWT } from "jose";
import type { Page } from "@playwright/test";

/**
 * Signs a test player in the way supabase-js stores a session in the browser, with a token the
 * test game server trusts. The app itself has no test-only sign-in path.
 */

export const PLAYER = "0f0f0f0f-1111-4222-8333-444455556666";
const AUTH_URL = "http://auth.e2e.test";

export async function playerToken(): Promise<string> {
  const secret = process.env.E2E_JWT_SECRET;
  if (!secret) throw new Error("E2E_JWT_SECRET is not set");
  return new SignJWT({ role: "authenticated", is_anonymous: true })
    .setProtectedHeader({ alg: "HS256" })
    .setSubject(PLAYER)
    .setAudience("authenticated")
    .setIssuer(`${AUTH_URL}/auth/v1`)
    .setIssuedAt()
    .setExpirationTime("2h")
    .sign(new TextEncoder().encode(secret));
}

export async function signIn(page: Page): Promise<string> {
  const token = await playerToken();
  const now = Math.floor(Date.now() / 1000);
  const session = {
    access_token: token,
    token_type: "bearer",
    expires_in: 7200,
    expires_at: now + 7200,
    refresh_token: "e2e-refresh-token",
    user: {
      id: PLAYER,
      aud: "authenticated",
      role: "authenticated",
      is_anonymous: true,
      app_metadata: {},
      user_metadata: {},
      created_at: new Date().toISOString(),
    },
  };
  const key = `sb-${new URL(AUTH_URL).hostname.split(".")[0]}-auth-token`;
  await page.addInitScript(([k, v]) => window.localStorage.setItem(k, v), [
    key,
    JSON.stringify(session),
  ] as const);
  return token;
}

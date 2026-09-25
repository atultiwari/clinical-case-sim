import "server-only";

import { cookies, headers } from "next/headers";

import { parseAuthConfig, type AuthConfig } from "@/lib/auth/config";
import { isSameOrigin, sessionCookie, type CookieSettings } from "@/lib/auth/request";
import { authenticate } from "@/lib/auth/session";
import { LoginRateLimiter } from "@/lib/auth/rate-limit";
import { isWriterConfigured } from "@/server/writer-db";

type Cached = { key: string; config: AuthConfig };
const globalForAuth = globalThis as unknown as { caseStudioAuth?: Cached; caseStudioLimiter?: LoginRateLimiter };

/** The login configuration from the environment, parsed once per value. */
export function getAuthConfig(): AuthConfig {
  const users = process.env.STUDIO_USERS ?? "";
  const secret = process.env.STUDIO_SESSION_SECRET ?? "";
  const key = `${users}\u0000${secret}`;
  const cached = globalForAuth.caseStudioAuth;
  if (cached && cached.key === key) return cached.config;
  const config = parseAuthConfig({ STUDIO_USERS: users, STUDIO_SESSION_SECRET: secret });
  if (config.mode === "invalid") console.error(`Case Studio: login misconfigured: ${config.reason}`);
  globalForAuth.caseStudioAuth = { key, config };
  return config;
}

/** One limiter per process (README: single instance). */
export function loginLimiter(): LoginRateLimiter {
  globalForAuth.caseStudioLimiter ??= new LoginRateLimiter();
  return globalForAuth.caseStudioLimiter;
}

export async function cookieSettings(): Promise<CookieSettings> {
  const h = await headers();
  return sessionCookie(h.get("host"), process.env.NODE_ENV);
}

/** The logged-in username, or null (always null without a login configured). */
export async function currentUser(): Promise<string | null> {
  const config = getAuthConfig();
  if (config.mode !== "login") return null;
  const { name } = await cookieSettings();
  return authenticate(config, (await cookies()).get(name)?.value);
}

export type WriteAvailability = { enabled: true } | { enabled: false; reason: string };

/** Whether the Studio can record decisions at all (not whether this request may). */
export function writeAvailability(): WriteAvailability {
  const config = getAuthConfig();
  if (config.mode !== "login") {
    return { enabled: false, reason: "Read-only: the Studio has no login configured (STUDIO_USERS), so it cannot record decisions." };
  }
  if (!isWriterConfigured()) {
    return { enabled: false, reason: "Read-only: CASE_VAULT_DB_URL_STUDIO_WRITER is not set, so the Studio cannot record decisions." };
  }
  return { enabled: true };
}

export class NotAllowedError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "NotAllowedError";
  }
}

/**
 * The gate for every write, run inside each server action: writes enabled, the
 * request from this site (Origin), and a valid session. Returns the username.
 */
export async function requireWriter(): Promise<string> {
  const availability = writeAvailability();
  if (!availability.enabled) throw new NotAllowedError(availability.reason);
  if (!isSameOrigin(await headers())) throw new NotAllowedError("Refused: the request did not come from the Studio's own pages.");
  const username = await currentUser();
  if (!username) throw new NotAllowedError("Your session has ended. Log in again.");
  return username;
}

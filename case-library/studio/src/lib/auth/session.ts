// Signed session cookies: <payload, base64url JSON>.<HMAC-SHA256 of the payload, base64url>.
// Stateless: logging out clears the cookie; rotating STUDIO_SESSION_SECRET or a
// password (passwordVersion) ends every older session.

import { createHmac, timingSafeEqual } from "node:crypto";

import type { AuthConfig } from "@/lib/auth/config";

export const SESSION_TTL_SECONDS = 12 * 60 * 60;
/** Allowance for a clock that moved backwards between signing and checking. */
const CLOCK_SKEW_SECONDS = 60;
const MAX_TOKEN_LENGTH = 1024;
const SIGNATURE_BYTES = 32;
const BASE64URL = /^[A-Za-z0-9_-]+$/;

export type SessionPayload = {
  v: 1;
  /** Username. */
  u: string;
  /** Password version of the account when the session began. */
  pv: string;
  /** Issued at and expires at, in seconds since the epoch. */
  iat: number;
  exp: number;
};

function sign(data: string, secret: string): Buffer {
  return createHmac("sha256", secret).update(data).digest();
}

export function nowSeconds(): number {
  return Math.floor(Date.now() / 1000);
}

export function createSessionToken(
  username: string,
  passwordVersion: string,
  secret: string,
  now: number = nowSeconds(),
): string {
  const payload: SessionPayload = { v: 1, u: username, pv: passwordVersion, iat: now, exp: now + SESSION_TTL_SECONDS };
  const data = Buffer.from(JSON.stringify(payload), "utf8").toString("base64url");
  return `${data}.${sign(data, secret).toString("base64url")}`;
}

function isPayload(value: unknown): value is SessionPayload {
  if (typeof value !== "object" || value === null) return false;
  const p = value as Record<string, unknown>;
  return (
    p.v === 1 &&
    typeof p.u === "string" &&
    typeof p.pv === "string" &&
    Number.isInteger(p.iat) &&
    Number.isInteger(p.exp)
  );
}

/** The payload of a token with a valid signature that has not expired; otherwise null. */
export function verifySessionToken(
  token: string | undefined,
  secret: string,
  now: number = nowSeconds(),
): SessionPayload | null {
  if (!token || token.length > MAX_TOKEN_LENGTH) return null;
  const parts = token.split(".");
  if (parts.length !== 2) return null;
  const [data, signature] = parts as [string, string];
  if (!BASE64URL.test(data) || !BASE64URL.test(signature)) return null;

  const given = Buffer.from(signature, "base64url");
  const expected = sign(data, secret);
  if (given.length !== SIGNATURE_BYTES || !timingSafeEqual(given, expected)) return null;

  let payload: unknown;
  try {
    payload = JSON.parse(Buffer.from(data, "base64url").toString("utf8"));
  } catch {
    return null;
  }
  if (!isPayload(payload)) return null;
  if (payload.exp <= now) return null;
  if (payload.iat > now + CLOCK_SKEW_SECONDS) return null;
  if (payload.exp - payload.iat > SESSION_TTL_SECONDS) return null;
  return payload;
}

/** The logged-in username for a cookie value, or null. Checks that the account and its password are unchanged. */
export function authenticate(config: AuthConfig, token: string | undefined, now: number = nowSeconds()): string | null {
  if (config.mode !== "login") return null;
  const payload = verifySessionToken(token, config.secret, now);
  if (!payload) return null;
  const user = config.users.get(payload.u);
  if (!user) return null;
  const a = Buffer.from(user.passwordVersion);
  const b = Buffer.from(payload.pv);
  return a.length === b.length && timingSafeEqual(a, b) ? user.username : null;
}

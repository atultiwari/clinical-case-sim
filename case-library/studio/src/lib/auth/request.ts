// Request details the guard and the server actions share: the session cookie's
// name and flags, whether a host is local, the client's address and the Origin check.

import { SESSION_TTL_SECONDS } from "@/lib/auth/session";

/** With Secure: the __Host- prefix makes the browser insist on Secure, Path=/ and no Domain. */
export const SECURE_COOKIE_NAME = "__Host-studio_session";
/** Only in development on http://localhost, where a Secure cookie would not be sent. */
export const LOCAL_COOKIE_NAME = "studio_session";

const LOCAL_HOSTNAMES = new Set(["localhost", "127.0.0.1", "[::1]", "::1"]);

/** The hostname of a Host header value, lower-cased, without the port. */
export function hostnameOf(host: string | null | undefined): string {
  if (!host) return "";
  const value = host.trim().toLowerCase();
  if (value.startsWith("[")) {
    const end = value.indexOf("]");
    return end > 0 ? value.slice(0, end + 1) : value;
  }
  return value.split(":")[0] ?? "";
}

export function isLocalHost(host: string | null | undefined): boolean {
  return LOCAL_HOSTNAMES.has(hostnameOf(host));
}

export type CookieSettings = {
  name: string;
  options: {
    httpOnly: true;
    secure: boolean;
    sameSite: "strict";
    path: "/";
    maxAge: number;
  };
};

/** Secure everywhere except the development server on localhost over http. */
export function sessionCookie(host: string | null | undefined, nodeEnv: string | undefined): CookieSettings {
  const secure = !(nodeEnv === "development" && isLocalHost(host));
  return {
    name: secure ? SECURE_COOKIE_NAME : LOCAL_COOKIE_NAME,
    options: { httpOnly: true, secure, sameSite: "strict", path: "/", maxAge: SESSION_TTL_SECONDS },
  };
}

type HeaderSource = { get(name: string): string | null };

/**
 * The client's address for rate limiting. Behind the reverse proxy (the Studio
 * binds to localhost), the proxy appends the address it saw to X-Forwarded-For,
 * so the last entry is the trustworthy one.
 */
export function clientAddress(headers: HeaderSource): string {
  const forwarded = headers.get("x-forwarded-for");
  const last = forwarded?.split(",").map((part) => part.trim()).filter(Boolean).at(-1);
  const address = last ?? headers.get("x-real-ip")?.trim() ?? "";
  return address.slice(0, 64) || "unknown";
}

/**
 * True when the request's Origin names the host it was sent to. Server actions
 * and the login form are refused otherwise (cross-site request forgery).
 */
export function isSameOrigin(headers: HeaderSource): boolean {
  const origin = headers.get("origin");
  const host = headers.get("x-forwarded-host") ?? headers.get("host");
  if (!origin || !host || origin === "null") return false;
  try {
    const url = new URL(origin);
    if (url.protocol !== "https:" && url.protocol !== "http:") return false;
    return url.host.toLowerCase() === host.trim().toLowerCase();
  } catch {
    return false;
  }
}

/** A safe path to return to after logging in: same site, no scheme, no '//' prefix. */
export function safeNextPath(value: unknown): string {
  if (typeof value !== "string" || value.length > 512) return "/";
  if (!/^\/(?![/\\])[A-Za-z0-9/@%._~?=&-]*$/.test(value)) return "/";
  if (value.startsWith("/login")) return "/";
  return value;
}

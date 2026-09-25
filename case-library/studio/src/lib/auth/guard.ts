// The access rule for every request, applied by src/proxy.ts (a pure function, so
// the allow/deny matrix is tested on its own).
//
// Server actions are POST requests to the page that holds them, and a POST to
// /login is let through without a session so that the login form works. That
// POST could name any action, so every server action also checks the session
// itself (src/server/auth.ts); the guard is the outer wall, not the only one.

import type { AuthConfig } from "@/lib/auth/config";

export const LOGIN_PATH = "/login";

export type GuardInput = {
  mode: AuthConfig["mode"];
  pathname: string;
  method: string;
  /** Whether the request carries a valid session cookie. */
  authenticated: boolean;
  /** Whether the Host header names this machine (localhost). */
  localHost: boolean;
};

export type GuardDecision =
  | { action: "allow" }
  | { action: "redirect"; location: string }
  | { action: "deny"; status: 401 | 403 | 500; message: string };

const ALLOW = { action: "allow" } as const;

export const MISCONFIGURED_MESSAGE =
  "The Case Studio's login is misconfigured, so it refuses every request. See the server log and case-library/studio/README.md.";
export const OPEN_MODE_REMOTE_MESSAGE =
  "The Case Studio has no login configured (STUDIO_USERS), so it answers only on localhost. See case-library/studio/README.md.";
export const UNAUTHENTICATED_MESSAGE = "Log in first.";

function isReadMethod(method: string): boolean {
  return method === "GET" || method === "HEAD";
}

export function decide(input: GuardInput): GuardDecision {
  const { mode, pathname, method, authenticated, localHost } = input;

  if (mode === "invalid") return { action: "deny", status: 500, message: MISCONFIGURED_MESSAGE };

  if (mode === "open") {
    // v1: read-only, no login. A safety net for a deployment that forgot
    // STUDIO_USERS: answer only requests addressed to localhost.
    if (!localHost) return { action: "deny", status: 403, message: OPEN_MODE_REMOTE_MESSAGE };
    if (pathname === LOGIN_PATH) return { action: "redirect", location: "/" };
    return ALLOW;
  }

  if (pathname === LOGIN_PATH) {
    if (authenticated && isReadMethod(method)) return { action: "redirect", location: "/" };
    return ALLOW;
  }
  if (authenticated) return ALLOW;
  if (isReadMethod(method)) {
    return { action: "redirect", location: `${LOGIN_PATH}?next=${encodeURIComponent(pathname)}` };
  }
  return { action: "deny", status: 401, message: UNAUTHENTICATED_MESSAGE };
}

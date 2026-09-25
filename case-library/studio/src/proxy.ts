// The Studio's guard (Next.js Proxy, formerly Middleware): every page, route
// handler and server action passes through here. With STUDIO_USERS set, only a
// valid session gets past it (except the login page); without it, the Studio is
// v1, read-only and answering on localhost only. The rule is in lib/auth/guard.ts.

import { NextResponse, type NextRequest } from "next/server";

import { parseAuthConfig, type AuthConfig } from "@/lib/auth/config";
import { decide } from "@/lib/auth/guard";
import { isLocalHost, sessionCookie } from "@/lib/auth/request";
import { authenticate } from "@/lib/auth/session";

let cached: { key: string; config: AuthConfig } | undefined;

function authConfig(): AuthConfig {
  const users = process.env.STUDIO_USERS ?? "";
  const secret = process.env.STUDIO_SESSION_SECRET ?? "";
  const key = `${users}\u0000${secret}`;
  if (!cached || cached.key !== key) {
    cached = { key, config: parseAuthConfig({ STUDIO_USERS: users, STUDIO_SESSION_SECRET: secret }) };
  }
  return cached.config;
}

export function proxy(request: NextRequest) {
  const auth = authConfig();
  const host = request.headers.get("host");
  const cookie = sessionCookie(host, process.env.NODE_ENV);
  const decision = decide({
    mode: auth.mode,
    pathname: request.nextUrl.pathname,
    method: request.method,
    authenticated: authenticate(auth, request.cookies.get(cookie.name)?.value) !== null,
    localHost: isLocalHost(host),
  });

  if (decision.action === "allow") return NextResponse.next();
  if (decision.action === "redirect") return NextResponse.redirect(new URL(decision.location, request.url), 303);
  return new NextResponse(decision.message, {
    status: decision.status,
    headers: { "content-type": "text/plain; charset=utf-8", "cache-control": "no-store" },
  });
}

export const config = {
  // Everything except the build's static files (which hold no case data).
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};

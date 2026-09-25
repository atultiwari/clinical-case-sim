"use server";

import { cookies, headers } from "next/headers";
import { redirect } from "next/navigation";

import type { ActionState } from "@/lib/action-state";
import { LOGIN_PATH } from "@/lib/auth/guard";
import { MAX_PASSWORD_LENGTH, verifyPassword } from "@/lib/auth/password";
import { loginKeys } from "@/lib/auth/rate-limit";
import { clientAddress, isSameOrigin, safeNextPath } from "@/lib/auth/request";
import { createSessionToken } from "@/lib/auth/session";
import { cookieSettings, getAuthConfig, loginLimiter } from "@/server/auth";

/** One message for every failure: wrong name, wrong password or locked out. */
const LOGIN_FAILED = "Login failed. Check the username and password, or wait 15 minutes and try again.";
const MAX_USERNAME_LENGTH = 64;

function field(form: FormData, name: string, max: number): string | null {
  const value = form.get(name);
  return typeof value === "string" && value.length <= max ? value : null;
}

export async function login(_previous: ActionState, form: FormData): Promise<ActionState> {
  const config = getAuthConfig();
  if (config.mode !== "login") return { ok: false, message: "This Studio has no login configured." };

  const h = await headers();
  if (!isSameOrigin(h)) return { ok: false, message: LOGIN_FAILED };

  const username = (field(form, "username", MAX_USERNAME_LENGTH) ?? "").trim().toLowerCase();
  const password = field(form, "password", MAX_PASSWORD_LENGTH) ?? "";
  const keys = loginKeys(clientAddress(h), username);
  const limiter = loginLimiter();
  if (limiter.isLocked(keys)) return { ok: false, message: LOGIN_FAILED };

  // scrypt runs for unknown usernames too (against a dummy entry of the same cost),
  // so the response time does not reveal which usernames exist.
  const user = config.users.get(username);
  const matches = await verifyPassword(password, user?.hash ?? config.dummy);
  if (!user || !matches) {
    limiter.recordFailure(keys);
    return { ok: false, message: LOGIN_FAILED };
  }

  limiter.recordSuccess(keys);
  const { name, options } = await cookieSettings();
  (await cookies()).set(name, createSessionToken(user.username, user.passwordVersion, config.secret), options);
  redirect(safeNextPath(form.get("next")));
}

export async function logout(): Promise<void> {
  const { name, options } = await cookieSettings();
  // Clearing the cookie needs no Origin check: at worst a forged request logs Atul out.
  (await cookies()).set(name, "", { ...options, maxAge: 0 });
  redirect(LOGIN_PATH);
}

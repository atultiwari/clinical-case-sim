// The Studio's login configuration, read from the environment (README: "Deploying").
//
//   STUDIO_USERS           username:scrypt$N$r$p$salt$hash, comma-separated
//   STUDIO_SESSION_SECRET  at least 32 bytes; required when STUDIO_USERS is set
//
// Without STUDIO_USERS the Studio runs as v1: read-only and without a login.
// Anything malformed makes the configuration invalid, and the guard then refuses
// every request (it fails closed). Messages never contain a hash or a secret.

import { createHash } from "node:crypto";

import { dummyHash, parseScryptHash, type ScryptHash } from "@/lib/auth/password";

export const USERS_VARIABLE = "STUDIO_USERS";
export const SECRET_VARIABLE = "STUDIO_SESSION_SECRET";
export const MIN_SECRET_BYTES = 32;
const MAX_USERS = 20;

/** Lower-case letters, digits, '_' and '-'; it also forms part of a batch id. */
export const USERNAME_PATTERN = /^[a-z][a-z0-9_-]{0,31}$/;

export type StudioUser = {
  username: string;
  hash: ScryptHash;
  /** Changes when the password changes, so older sessions stop working. */
  passwordVersion: string;
};

export type AuthConfig =
  | { mode: "open" }
  | {
      mode: "login";
      users: ReadonlyMap<string, StudioUser>;
      secret: string;
      /** Checked for unknown usernames, at the same cost as a real entry. */
      dummy: ScryptHash;
    }
  | { mode: "invalid"; reason: string };

export function passwordVersion(entry: string): string {
  return createHash("sha256").update(entry).digest("base64url").slice(0, 16);
}

function parseUsers(raw: string): ReadonlyMap<string, StudioUser> | string {
  const entries = raw.split(",").map((part) => part.trim()).filter(Boolean);
  if (entries.length === 0) return `${USERS_VARIABLE} holds no accounts`;
  if (entries.length > MAX_USERS) return `${USERS_VARIABLE} holds more than ${MAX_USERS} accounts`;
  const users = new Map<string, StudioUser>();
  for (const [index, entry] of entries.entries()) {
    const colon = entry.indexOf(":");
    const username = colon > 0 ? entry.slice(0, colon) : "";
    const encoded = colon > 0 ? entry.slice(colon + 1) : "";
    if (!USERNAME_PATTERN.test(username)) {
      return `${USERS_VARIABLE} entry ${index + 1}: the username must match ${USERNAME_PATTERN.source}`;
    }
    const hash = parseScryptHash(encoded);
    if (!hash) return `${USERS_VARIABLE} entry ${index + 1} (${username}): the hash is not a valid scrypt entry`;
    if (users.has(username)) return `${USERS_VARIABLE}: ${username} appears twice`;
    users.set(username, { username, hash, passwordVersion: passwordVersion(encoded) });
  }
  return users;
}

export function parseAuthConfig(env: Readonly<Record<string, string | undefined>>): AuthConfig {
  const rawUsers = env[USERS_VARIABLE]?.trim();
  if (!rawUsers) return { mode: "open" };

  const users = parseUsers(rawUsers);
  if (typeof users === "string") return { mode: "invalid", reason: users };

  const secret = env[SECRET_VARIABLE] ?? "";
  if (Buffer.byteLength(secret, "utf8") < MIN_SECRET_BYTES) {
    return {
      mode: "invalid",
      reason: `${SECRET_VARIABLE} must be set to at least ${MIN_SECRET_BYTES} bytes when ${USERS_VARIABLE} is set`,
    };
  }

  const first = users.values().next().value as StudioUser;
  return { mode: "login", users, secret, dummy: dummyHash(first.hash) };
}

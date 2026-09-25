// Password hashing with scrypt from node:crypto (no dependencies).
// Stored form: scrypt$N$r$p$<salt, base64>$<hash, base64>.
// Imported by scripts/hash-password.ts through Node's type stripping, so this
// file uses only erasable TypeScript and imports nothing but node:crypto.

import { randomBytes, scrypt, timingSafeEqual } from "node:crypto";

export type ScryptParams = { N: number; r: number; p: number };

export type ScryptHash = ScryptParams & { salt: Buffer; hash: Buffer };

/**
 * The default for new entries: N=2^15, r=8, p=1 (32 MiB and roughly 100 ms per
 * check). Stronger than Node's default N=2^14, and small enough that a burst of
 * login attempts cannot exhaust a small VPS's memory.
 */
export const DEFAULT_SCRYPT_PARAMS: ScryptParams = Object.freeze({ N: 2 ** 15, r: 8, p: 1 });

const KEY_LENGTH = 32;
const SALT_LENGTH = 16;
// Bounds on what a stored entry may ask for, so a bad entry cannot exhaust memory.
const MIN_LOG_N = 14;
const MAX_LOG_N = 20;
const MAX_R = 32;
const MAX_P = 16;
const MAX_MEMORY_BYTES = 512 * 1024 * 1024;
/** Longer passwords are refused before hashing. */
export const MAX_PASSWORD_LENGTH = 1024;

const BASE64 = /^[A-Za-z0-9+/]+={0,2}$/;
const POSITIVE_INT = /^[1-9][0-9]{0,9}$/;

function memoryFor({ N, r }: ScryptParams): number {
  return 128 * N * r;
}

function validParams(params: ScryptParams): boolean {
  const { N, r, p } = params;
  const logN = Math.log2(N);
  return (
    Number.isInteger(logN) &&
    logN >= MIN_LOG_N &&
    logN <= MAX_LOG_N &&
    r >= 1 &&
    r <= MAX_R &&
    p >= 1 &&
    p <= MAX_P &&
    memoryFor(params) <= MAX_MEMORY_BYTES
  );
}

/** Parses a stored entry; null if it is malformed or asks for unsafe parameters. */
export function parseScryptHash(encoded: string): ScryptHash | null {
  const parts = encoded.split("$");
  if (parts.length !== 6 || parts[0] !== "scrypt") return null;
  const [, n, r, p, salt, hash] = parts as [string, string, string, string, string, string];
  if (![n, r, p].every((part) => POSITIVE_INT.test(part))) return null;
  if (!BASE64.test(salt) || !BASE64.test(hash)) return null;
  const params = { N: Number(n), r: Number(r), p: Number(p) };
  if (!validParams(params)) return null;
  const saltBytes = Buffer.from(salt, "base64");
  const hashBytes = Buffer.from(hash, "base64");
  if (saltBytes.length < SALT_LENGTH || hashBytes.length !== KEY_LENGTH) return null;
  return { ...params, salt: saltBytes, hash: hashBytes };
}

function derive(password: string, salt: Buffer, params: ScryptParams): Promise<Buffer> {
  return new Promise((resolve, reject) => {
    scrypt(
      password.normalize("NFC"),
      salt,
      KEY_LENGTH,
      { N: params.N, r: params.r, p: params.p, maxmem: memoryFor(params) * 2 },
      (error, key) => (error ? reject(error) : resolve(key)),
    );
  });
}

export function formatScryptHash({ N, r, p, salt, hash }: ScryptHash): string {
  return ["scrypt", N, r, p, salt.toString("base64"), hash.toString("base64")].join("$");
}

/** Hashes a new password with a random salt. */
export async function hashPassword(
  password: string,
  params: ScryptParams = DEFAULT_SCRYPT_PARAMS,
): Promise<string> {
  if (!validParams(params)) throw new Error("Unsafe scrypt parameters");
  if (password.length === 0 || password.length > MAX_PASSWORD_LENGTH) {
    throw new Error(`A password must have 1 to ${MAX_PASSWORD_LENGTH} characters`);
  }
  const salt = randomBytes(SALT_LENGTH);
  const hash = await derive(password, salt, params);
  return formatScryptHash({ ...params, salt, hash });
}

/**
 * Checks a password against a parsed entry in constant time. Always runs scrypt
 * once, so a caller can check unknown usernames against a dummy entry and take
 * the same time as for a real one.
 */
export async function verifyPassword(password: string, stored: ScryptHash): Promise<boolean> {
  const candidate = password.length > MAX_PASSWORD_LENGTH ? "" : password;
  const derived = await derive(candidate, stored.salt, stored);
  const same = derived.length === stored.hash.length && timingSafeEqual(derived, stored.hash);
  return same && candidate.length > 0 && candidate === password;
}

/** An entry no password matches, with the given cost: for unknown usernames. */
export function dummyHash(params: ScryptParams = DEFAULT_SCRYPT_PARAMS): ScryptHash {
  return { ...params, salt: randomBytes(SALT_LENGTH), hash: randomBytes(KEY_LENGTH) };
}

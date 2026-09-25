import "server-only";

import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { parseEnv } from "node:util";

export const DB_URL_VARIABLE = "CASE_VAULT_DB_URL_READONLY";
export const WRITER_DB_URL_VARIABLE = "CASE_VAULT_DB_URL_STUDIO_WRITER";

/** The only variables the Studio takes from case-library/.env (which also holds the backup URL). */
const FROM_CASE_LIBRARY_ENV = new Set([DB_URL_VARIABLE, WRITER_DB_URL_VARIABLE]);

/**
 * A server-only variable. Next.js loads `studio/.env.local` itself; if a database
 * URL is still missing, that one line is read from `case-library/.env` (and
 * nothing else from that file).
 */
function readServerVariable(name: string): string | undefined {
  const fromProcess = process.env[name]?.trim();
  if (fromProcess) return fromProcess;
  return FROM_CASE_LIBRARY_ENV.has(name) ? readFromCaseLibraryEnv(name) : undefined;
}

/** The read-only Case Vault URL. */
export function readDatabaseUrl(): string | undefined {
  return readServerVariable(DB_URL_VARIABLE);
}

/** The Studio writer's Case Vault URL (v2). Without it the Studio cannot write. */
export function readWriterDatabaseUrl(): string | undefined {
  return readServerVariable(WRITER_DB_URL_VARIABLE);
}

function readFromCaseLibraryEnv(name: string): string | undefined {
  const file = path.resolve(process.cwd(), "..", ".env");
  if (!existsSync(file)) return undefined;
  try {
    const parsed = parseEnv(readFileSync(file, "utf8"));
    const value = parsed[name]?.trim();
    return value || undefined;
  } catch (error) {
    console.error(`Case Studio: could not read ${file}`, error);
    return undefined;
  }
}

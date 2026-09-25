import "server-only";

import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { parseEnv } from "node:util";

export const DB_URL_VARIABLE = "CASE_VAULT_DB_URL_READONLY";

/**
 * The read-only Case Vault URL. Next.js loads `studio/.env.local` itself; if the
 * variable is still missing, the one line is read from `case-library/.env`
 * (and nothing else from that file, which also holds the backup URL).
 */
export function readDatabaseUrl(): string | undefined {
  const fromProcess = process.env[DB_URL_VARIABLE]?.trim();
  if (fromProcess) return fromProcess;
  return readFromCaseLibraryEnv();
}

function readFromCaseLibraryEnv(): string | undefined {
  const file = path.resolve(process.cwd(), "..", ".env");
  if (!existsSync(file)) return undefined;
  try {
    const parsed = parseEnv(readFileSync(file, "utf8"));
    const value = parsed[DB_URL_VARIABLE]?.trim();
    return value || undefined;
  } catch (error) {
    console.error(`Case Studio: could not read ${file}`, error);
    return undefined;
  }
}

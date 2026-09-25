import "server-only";

import postgres from "postgres";

import { describeDatabaseHost, type DatabaseHost } from "@/lib/db-host";
import { DB_URL_VARIABLE, readDatabaseUrl } from "@/server/env";

/** The role every Studio query runs as (migration 20260925210000). */
const READER_ROLE = "casevault_reader";

export type Reader = postgres.TransactionSql;

export class MissingDatabaseUrlError extends Error {
  constructor() {
    super(`${DB_URL_VARIABLE} is not set. See case-library/studio/README.md.`);
    this.name = "MissingDatabaseUrlError";
  }
}

type Client = postgres.Sql;
const globalForDb = globalThis as unknown as { caseStudioSql?: Client };

function client(): Client {
  if (globalForDb.caseStudioSql) return globalForDb.caseStudioSql;
  const url = readDatabaseUrl();
  if (!url) throw new MissingDatabaseUrlError();
  const sql = postgres(url, {
    max: 3,
    idle_timeout: 30,
    connect_timeout: 10,
    // Works through Supabase's poolers as well as a direct connection.
    prepare: false,
    connection: { application_name: "case-studio" },
    onnotice: () => undefined,
  });
  // Reused across hot reloads in development, so reloads do not leak pools.
  globalForDb.caseStudioSql = sql;
  return sql;
}

export function isDatabaseConfigured(): boolean {
  return Boolean(readDatabaseUrl());
}

export function databaseHost(): DatabaseHost | null {
  const url = readDatabaseUrl();
  return url ? describeDatabaseHost(url) : null;
}

/**
 * Runs `fn` in a read-only transaction as casevault_reader. Every Studio query
 * goes through here, so even a superuser URL (the local database) cannot write:
 * the transaction is READ ONLY and the role has only SELECT and read functions.
 * Queries use tagged templates only, which send values as parameters.
 */
export async function withReader<T>(fn: (sql: Reader) => Promise<T>): Promise<T> {
  const sql = client();
  const result = await sql.begin("read only", async (tx) => {
    await tx`select set_config('role', ${READER_ROLE}, true)`;
    return fn(tx);
  });
  return result as T;
}

/** Closes the pool (tests and scripts). */
export async function closeDb(): Promise<void> {
  const sql = globalForDb.caseStudioSql;
  globalForDb.caseStudioSql = undefined;
  if (sql) await sql.end({ timeout: 5 });
}

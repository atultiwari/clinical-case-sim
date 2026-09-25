import "server-only";

import postgres from "postgres";

import { readWriterDatabaseUrl, WRITER_DB_URL_VARIABLE } from "@/server/env";

/** The role every Studio write runs as (migration 20260926090000). */
const WRITER_ROLE = "casevault_studio_writer";

export type Writer = postgres.TransactionSql;

export class MissingWriterUrlError extends Error {
  constructor() {
    super(`${WRITER_DB_URL_VARIABLE} is not set. See case-library/studio/README.md.`);
    this.name = "MissingWriterUrlError";
  }
}

type Client = postgres.Sql;
const globalForDb = globalThis as unknown as { caseStudioWriterSql?: Client };

function client(): Client {
  if (globalForDb.caseStudioWriterSql) return globalForDb.caseStudioWriterSql;
  const url = readWriterDatabaseUrl();
  if (!url) throw new MissingWriterUrlError();
  const sql = postgres(url, {
    max: 2,
    idle_timeout: 30,
    connect_timeout: 10,
    prepare: false,
    connection: { application_name: "case-studio-writer" },
    onnotice: () => undefined,
  });
  globalForDb.caseStudioWriterSql = sql;
  return sql;
}

export function isWriterConfigured(): boolean {
  return Boolean(readWriterDatabaseUrl());
}

/**
 * Runs `fn` in its own read-write transaction as casevault_studio_writer, which
 * may only insert review decisions and set figure decisions (column grants and
 * row-level security). Queries use tagged templates only, so values are parameters.
 */
export async function withWriter<T>(fn: (sql: Writer) => Promise<T>): Promise<T> {
  const sql = client();
  const result = await sql.begin("read write", async (tx) => {
    await tx`select set_config('role', ${WRITER_ROLE}, true)`;
    return fn(tx);
  });
  return result as T;
}

/** Closes the pool (tests). */
export async function closeWriterDb(): Promise<void> {
  const sql = globalForDb.caseStudioWriterSql;
  globalForDb.caseStudioWriterSql = undefined;
  if (sql) await sql.end({ timeout: 5 });
}

import { resolve } from "node:path";
import { z } from "zod";

/** The game server's environment (see .env.example). Checked once at start-up. */

const Env = z
  .object({
    NODE_ENV: z.string().default("development"),
    NIDANA_BUNDLE_SOURCE: z.enum(["files", "database"]).default("files"),
    NIDANA_STORE: z.enum(["memory", "database"]).default("memory"),
    NIDANA_EXPORTS_DIR: z.string().optional(),
    NIDANA_CATALOGUE_PATH: z.string().optional(),
    NIDANA_CONFIG_DIR: z.string().optional(),
    DATABASE_URL: z.string().optional(),
    SUPABASE_URL: z.url().optional(),
    SUPABASE_JWT_SECRET: z.string().optional(),
  })
  .superRefine((env, ctx) => {
    const needsDb =
      env.NIDANA_BUNDLE_SOURCE === "database" ||
      env.NIDANA_STORE === "database";
    if (needsDb && !env.DATABASE_URL) {
      ctx.addIssue({
        code: "custom",
        path: ["DATABASE_URL"],
        message: "required when bundles or play data come from the database",
      });
    }
    if (env.NODE_ENV === "production" && env.NIDANA_STORE === "memory") {
      ctx.addIssue({
        code: "custom",
        path: ["NIDANA_STORE"],
        message: "play data must be stored in the database in production",
      });
    }
    if (!env.SUPABASE_URL) {
      ctx.addIssue({
        code: "custom",
        path: ["SUPABASE_URL"],
        message:
          "required: sign-in tokens are checked against this project (their issuer)",
      });
    }
  });

export interface ServerConfig {
  readonly bundleSource: "files" | "database";
  readonly store: "memory" | "database";
  readonly exportsDir: string;
  readonly cataloguePath: string;
  readonly configDir: string;
  readonly databaseUrl: string | null;
  readonly jwtSecret: string | null;
  readonly jwksUrl: string;
  readonly issuer: string;
}

/** Paths default to the monorepo layout, relative to apps/server (where Next runs). */
export function loadConfig(
  env: Record<string, string | undefined>,
  cwd: string = process.cwd(),
): ServerConfig {
  const parsed = Env.safeParse(env);
  if (!parsed.success)
    throw new Error(
      `Game server configuration: ${z.prettifyError(parsed.error)}`,
    );
  const e = parsed.data;
  const nidana = resolve(cwd, "../..");
  const auth = (e.SUPABASE_URL ?? "").replace(/\/$/, "");
  return {
    bundleSource: e.NIDANA_BUNDLE_SOURCE,
    store: e.NIDANA_STORE,
    exportsDir: resolve(
      cwd,
      e.NIDANA_EXPORTS_DIR ?? resolve(nidana, "../case-library/exports"),
    ),
    cataloguePath: resolve(
      cwd,
      e.NIDANA_CATALOGUE_PATH ??
        resolve(nidana, "conformance/catalogue/catalogue.v2.json"),
    ),
    configDir: resolve(cwd, e.NIDANA_CONFIG_DIR ?? resolve(nidana, "configs")),
    databaseUrl: e.DATABASE_URL ?? null,
    jwtSecret: e.SUPABASE_JWT_SECRET ?? null,
    jwksUrl: `${auth}/auth/v1/.well-known/jwks.json`,
    issuer: `${auth}/auth/v1`,
  };
}

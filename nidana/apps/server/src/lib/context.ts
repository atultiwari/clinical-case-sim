import { randomUUID } from "node:crypto";
import { readFile } from "node:fs/promises";
import { join } from "node:path";
import {
  parseCatalogueJson,
  PINNED_CATALOGUE_VERSION,
} from "@nidana/contracts";
import { parseDifficultySettings, parseScoringSettings } from "@nidana/engine";
import postgres from "postgres";
import { createVerifier, type Verifier } from "./auth";
import { fileBundleSource } from "./bundles";
import { loadConfig } from "./config";
import type { GameDeps } from "./game";
import { pgBundleSource, pgStore } from "./pg";
import { createRateLimiter, type RateLimiter } from "./rate-limit";
import { createBundleRegistry } from "./registry";
import { memoryStore } from "./store";
import type { CatalogueExport } from "@nidana/contracts";

/** Everything a request needs, built once per server process. */
export interface ServerContext {
  readonly game: GameDeps;
  readonly catalogue: CatalogueExport;
  readonly verifier: Verifier;
  readonly limits: {
    readonly actions: RateLimiter;
    readonly starts: RateLimiter;
    readonly reads: RateLimiter;
  };
}

async function build(): Promise<ServerContext> {
  const config = loadConfig(process.env);
  const catalogueParsed = parseCatalogueJson(
    await readFile(config.cataloguePath, "utf8"),
  );
  if (!catalogueParsed.success) throw new Error(catalogueParsed.error.message);
  const catalogue = catalogueParsed.data;
  if (catalogue.version !== PINNED_CATALOGUE_VERSION) {
    throw new Error(
      `The catalogue is v${catalogue.version}; Nidana is pinned to v${PINNED_CATALOGUE_VERSION}`,
    );
  }
  const readJson = async (name: string): Promise<unknown> =>
    JSON.parse(await readFile(join(config.configDir, name), "utf8"));
  const sql =
    config.databaseUrl === null
      ? null
      : postgres(config.databaseUrl, { max: 5, prepare: false });
  const source =
    config.bundleSource === "database" && sql !== null
      ? pgBundleSource(sql)
      : fileBundleSource(config.exportsDir);
  const store =
    config.store === "database" && sql !== null ? pgStore(sql) : memoryStore();
  return {
    catalogue,
    game: {
      registry: createBundleRegistry(source, catalogue),
      store,
      settings: parseDifficultySettings(await readJson("difficulty.json")),
      scoring: parseScoringSettings(await readJson("scoring.json")),
      newId: randomUUID,
      now: () => new Date(),
    },
    verifier: createVerifier({
      ...(config.jwtSecret ? { jwtSecret: config.jwtSecret } : {}),
      ...(config.jwksUrl ? { jwksUrl: config.jwksUrl } : {}),
      ...(config.issuer ? { issuer: config.issuer } : {}),
    }),
    limits: {
      actions: createRateLimiter(120, 60_000),
      starts: createRateLimiter(20, 60 * 60_000),
      reads: createRateLimiter(300, 60_000),
    },
  };
}

let context: Promise<ServerContext> | null = null;

export function getContext(): Promise<ServerContext> {
  context ??= build().catch((error: unknown) => {
    context = null;
    throw error;
  });
  return context;
}

import { fileURLToPath } from "node:url";

export const EXPORTS_DIR = fileURLToPath(
  new URL("../../../../case-library/exports/", import.meta.url),
);
export const NIDANA_DIR = fileURLToPath(new URL("../../../", import.meta.url));

import { readFileSync } from "node:fs";
import { parseCatalogueJson } from "@nidana/contracts";
import {
  parseDifficultySettings,
  parseScoringSettings,
  type Action,
  type PreparedCase,
} from "@nidana/engine";
import { fileBundleSource } from "@/lib/bundles";
import type { GameDeps } from "@/lib/game";
import { createBundleRegistry } from "@/lib/registry";
import { memoryStore } from "@/lib/store";

const catalogueResult = parseCatalogueJson(
  readFileSync(`${NIDANA_DIR}conformance/catalogue/catalogue.v2.json`, "utf8"),
);
if (!catalogueResult.success) throw new Error(catalogueResult.error.message);
export const catalogue = catalogueResult.data;
export const settings = parseDifficultySettings(
  JSON.parse(readFileSync(`${NIDANA_DIR}configs/difficulty.json`, "utf8")),
);
export const scoring = parseScoringSettings(
  JSON.parse(readFileSync(`${NIDANA_DIR}configs/scoring.json`, "utf8")),
);
export const registry = createBundleRegistry(
  fileBundleSource(EXPORTS_DIR),
  catalogue,
);
export const PILOT = "PMC12949993@v1.r3";

export function benchmarkActions(): Action[] {
  const file = JSON.parse(
    readFileSync(
      `${NIDANA_DIR}conformance/PMC12949993/benchmark-path.json`,
      "utf8",
    ),
  ) as {
    actions: Action[];
  };
  return file.actions;
}

export async function pilot(): Promise<PreparedCase> {
  return registry.load(PILOT);
}

export function deps(
  overrides: Partial<GameDeps> = {},
): GameDeps & { store: ReturnType<typeof memoryStore> } {
  let next = 0;
  const store = memoryStore();
  return {
    registry,
    store,
    settings,
    scoring,
    newId: () => `enc-${(next += 1)}`,
    now: () => new Date("2026-09-26T12:00:00Z"),
    ...overrides,
  } as GameDeps & { store: ReturnType<typeof memoryStore> };
}

import { randomBytes } from "node:crypto";
import { SignJWT } from "jose";

/** A fresh signing key per test run, so no key is ever written in the repository. */
export const SECRET = randomBytes(32).toString("hex");

export async function tokenFor(
  sub: string,
  secret = SECRET,
  audience = "authenticated",
  expires = "1h",
): Promise<string> {
  return new SignJWT({ role: "authenticated" })
    .setProtectedHeader({ alg: "HS256" })
    .setSubject(sub)
    .setAudience(audience)
    .setIssuedAt()
    .setExpirationTime(expires)
    .sign(new TextEncoder().encode(secret));
}

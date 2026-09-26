import { readFileSync, readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import {
  parseBundleJson,
  parseCatalogueJson,
  type CaseBundle,
} from "@nidana/contracts";
import {
  parseDifficultySettings,
  parseScoringSettings,
  prepareCase,
  type PreparedCase,
} from "../src/index.ts";

const EXPORTS = fileURLToPath(
  new URL("../../../../case-library/exports/", import.meta.url),
);
const NIDANA = fileURLToPath(new URL("../../../", import.meta.url));

function unwrap<T>(result: {
  success: boolean;
  data: T | null;
  error: { message: string } | null;
}): T {
  if (!result.success || result.data === null)
    throw new Error(result.error?.message);
  return result.data;
}

export const catalogue = unwrap(
  parseCatalogueJson(
    readFileSync(`${NIDANA}conformance/catalogue/catalogue.v2.json`, "utf8"),
  ),
);

export const settings = parseDifficultySettings(
  JSON.parse(readFileSync(`${NIDANA}configs/difficulty.json`, "utf8")),
);

export const scoring = parseScoringSettings(
  JSON.parse(readFileSync(`${NIDANA}configs/scoring.json`, "utf8")),
);

export function loadBundle(name: string): CaseBundle {
  return unwrap(
    parseBundleJson(readFileSync(`${EXPORTS}${name}.json`, "utf8")),
  );
}

export function exportedBundleNames(): string[] {
  return readdirSync(EXPORTS)
    .filter((name) => name.endsWith(".json"))
    .map((name) => name.replace(/\.json$/, ""))
    .sort();
}

/** The newest published revision of each case, the one Nidana loads (changelog, 2026-09-26). */
export function newestBundleNames(): string[] {
  const newest = new Map<string, { name: string; revision: number }>();
  for (const name of exportedBundleNames()) {
    const match = /^(.+)\.r(\d+)$/.exec(name);
    if (match === null) continue;
    const [, version = "", revision = "0"] = match;
    const current = newest.get(version);
    if (current === undefined || Number(revision) > current.revision) {
      newest.set(version, { name, revision: Number(revision) });
    }
  }
  return [...newest.values()].map((entry) => entry.name).sort();
}

export function readConformance(path: string): unknown {
  return JSON.parse(readFileSync(`${NIDANA}conformance/${path}`, "utf8"));
}

let pilotCache: PreparedCase | undefined;
export const PILOT = "PMC12949993@v1.r3";

/** The pilot's newest revision, on the pinned catalogue. */
export function pilot(): PreparedCase {
  pilotCache ??= prepareCase(loadBundle(PILOT), catalogue);
  return pilotCache;
}

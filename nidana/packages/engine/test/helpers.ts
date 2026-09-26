import { readFileSync, readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import {
  parseBundleJson,
  parseCatalogueJson,
  type CaseBundle,
} from "@nidana/contracts";
import {
  parseDifficultySettings,
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

export function readConformance(path: string): unknown {
  return JSON.parse(readFileSync(`${NIDANA}conformance/${path}`, "utf8"));
}

let pilotCache: PreparedCase | undefined;
/** The pilot, PMC12949993@v1.r2, on the pinned catalogue. */
export function pilot(): PreparedCase {
  pilotCache ??= prepareCase(loadBundle("PMC12949993@v1.r2"), catalogue);
  return pilotCache;
}

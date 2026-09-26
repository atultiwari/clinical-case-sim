import { readFileSync, readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";

export const EXPORTS_DIR = fileURLToPath(
  new URL("../../../../case-library/exports/", import.meta.url),
);

export function readJson(relativeToTest: string): unknown {
  return JSON.parse(
    readFileSync(new URL(relativeToTest, import.meta.url), "utf8"),
  );
}

/** A deep copy of a fixture, so each test changes its own copy. */
export function fixture(name: "bundle" | "catalogue"): Record<string, unknown> {
  return readJson(`./fixtures/${name}.fixture.json`) as Record<string, unknown>;
}

export function exportedBundleFiles(): string[] {
  return readdirSync(EXPORTS_DIR)
    .filter((name) => name.endsWith(".json"))
    .sort();
}

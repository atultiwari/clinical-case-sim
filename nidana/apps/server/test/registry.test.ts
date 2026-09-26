import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { parseCatalogueJson } from "@nidana/contracts";
import { canonicalJson, sha256Hex } from "@/lib/canonical-json";
import {
  BundleRefusedError,
  fileBundleSource,
  storedFromBody,
  verifyBundle,
  type BundleSource,
  type StoredBundle,
} from "@/lib/bundles";
import { createBundleRegistry } from "@/lib/registry";
import { EXPORTS_DIR, NIDANA_DIR } from "./helpers";

const catalogueResult = parseCatalogueJson(
  readFileSync(`${NIDANA_DIR}conformance/catalogue/catalogue.v2.json`, "utf8"),
);
if (!catalogueResult.success) throw new Error(catalogueResult.error.message);
const catalogue = catalogueResult.data;
const files = fileBundleSource(EXPORTS_DIR);
const PILOT = "PMC12949993@v1.r3";

async function read(id: string): Promise<StoredBundle> {
  const stored = await files.read(id);
  if (stored === null) throw new Error(`${id} is missing`);
  return stored;
}

function pilotBody(): Record<string, unknown> {
  return JSON.parse(
    readFileSync(`${EXPORTS_DIR}${PILOT}.json`, "utf8"),
  ) as Record<string, unknown>;
}

function refusal(action: () => unknown): string | undefined {
  try {
    action();
  } catch (error: unknown) {
    if (error instanceof BundleRefusedError) return error.code;
    throw error;
  }
  return undefined;
}

describe("verifyBundle", () => {
  it("accepts a published bundle whose hash matches", async () => {
    const stored = await read(PILOT);
    expect(verifyBundle(stored, catalogue).bundle.bundle_id).toBe(PILOT);
  });

  it("accepts a bundle read back from the database's jsonb body", async () => {
    const stored = await read(PILOT);
    const fromDb = storedFromBody(PILOT, pilotBody(), stored.sha256);
    expect(verifyBundle(fromDb, catalogue).bundle.bundle_id).toBe(PILOT);
  });

  it("refuses a bundle whose hash does not match", async () => {
    const stored = await read(PILOT);
    const tampered = { ...stored, text: stored.text.replace('"72"', '"73"') };
    expect(refusal(() => verifyBundle(tampered, catalogue))).toBe(
      "hash_mismatch",
    );
  });

  it("refuses an unsupported schema version", () => {
    const text = canonicalJson({ ...pilotBody(), schema_version: "0.4" });
    expect(
      refusal(() =>
        verifyBundle({ id: PILOT, text, sha256: sha256Hex(text) }, catalogue),
      ),
    ).toBe("unsupported_schema");
  });

  it("refuses an unsupported catalogue version", async () => {
    const stored = await read("PMC12949993@v1.r1");
    expect(refusal(() => verifyBundle(stored, catalogue))).toBe(
      "unsupported_catalogue",
    );
  });

  it("refuses an invalid bundle and a file holding another bundle", () => {
    const text = canonicalJson({ ...pilotBody(), facts: "none" });
    expect(
      refusal(() =>
        verifyBundle({ id: PILOT, text, sha256: sha256Hex(text) }, catalogue),
      ),
    ).toBe("invalid_bundle");
    const other = canonicalJson({
      ...pilotBody(),
      bundle_id: "PMC12949993@v1.r9",
    });
    expect(
      refusal(() =>
        verifyBundle(
          { id: PILOT, text: other, sha256: sha256Hex(other) },
          catalogue,
        ),
      ),
    ).toBe("invalid_bundle");
  });
});

describe("the bundle registry", () => {
  const registry = createBundleRegistry(files, catalogue);

  it("serves the newest published revision of each case", async () => {
    const bySlug = await registry.newestBySlug();
    const ids = [...bySlug.values()].map((p) => p.bundle.bundle_id);
    expect(ids).toContain(PILOT);
    expect(ids).not.toContain("PMC12949993@v1.r2");
    expect(ids).toHaveLength(10);
  });

  it("lists case cards without source identifiers", async () => {
    const cards = await registry.cases();
    expect(cards).toHaveLength(10);
    expect(JSON.stringify(cards)).not.toMatch(/PMC\d|doi|10\.\d{4}/i);
    expect(cards.every((c) => /^c-[a-z0-9]{5}$/.test(c.slug))).toBe(true);
  });

  it("records the published bundles it refuses", async () => {
    const refused = await registry.refused();
    expect(refused).toEqual([
      expect.objectContaining({
        id: "PMC12949993@v1.r1",
        code: "unsupported_catalogue",
      }),
    ]);
  });

  it("refuses a bundle that is not published", async () => {
    await expect(registry.load("PMC1@v1.r1")).rejects.toMatchObject({
      code: "not_found",
    });
  });

  it("retries a bundle after a failed read", async () => {
    let calls = 0;
    const flaky: BundleSource = {
      listPublished: async () => [PILOT],
      read: async (id) => {
        calls += 1;
        if (calls === 1) return { id, text: "{}", sha256: "0".repeat(64) };
        return files.read(id);
      },
    };
    const retrying = createBundleRegistry(flaky, catalogue);
    await expect(retrying.load(PILOT)).rejects.toMatchObject({
      code: "hash_mismatch",
    });
    await expect(retrying.load(PILOT)).resolves.toMatchObject({
      bundle: { bundle_id: PILOT },
    });
  });
});

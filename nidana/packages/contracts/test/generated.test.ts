import { readFile } from "node:fs/promises";
import { describe, expect, it } from "vitest";
import {
  OUTPUT_PATH,
  SCHEMA_PATH,
  renderBundleModule,
} from "../scripts/render.ts";
import { PINNED_BUNDLE_SCHEMA_VERSION } from "../src/index.ts";

describe("the generated bundle contracts", () => {
  it("match the Case Library's schema (run `pnpm --filter @nidana/contracts generate`)", async () => {
    const committed = await readFile(OUTPUT_PATH, "utf8");
    expect(committed).toBe(await renderBundleModule());
  });

  it("come from the pinned schema version", async () => {
    const schema = JSON.parse(await readFile(SCHEMA_PATH, "utf8")) as {
      properties: { schema_version: { const: string } };
    };
    expect(schema.properties.schema_version.const).toBe(
      PINNED_BUNDLE_SCHEMA_VERSION,
    );
  });
});

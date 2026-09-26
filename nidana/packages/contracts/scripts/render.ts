import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { format } from "prettier";
import { generateZodModule } from "./json-schema-to-zod.ts";

/** The pinned bundle schema (nidana/CLAUDE.md), read from the Case Library. */
export const SCHEMA_PATH = fileURLToPath(
  new URL(
    "../../../../case-library/schemas/case-bundle.v0.3.schema.json",
    import.meta.url,
  ),
);
export const OUTPUT_PATH = fileURLToPath(
  new URL("../src/generated/case-bundle.ts", import.meta.url),
);

const HEADER = `// Generated from case-library/schemas/case-bundle.v0.3.schema.json by
// \`pnpm --filter @nidana/contracts generate\`. Do not edit by hand; a test checks it is current.
/* eslint-disable */`;

/** The generated module for the pinned schema, formatted as it is committed. */
export async function renderBundleModule(): Promise<string> {
  const schema: unknown = JSON.parse(await readFile(SCHEMA_PATH, "utf8"));
  if (typeof schema !== "object" || schema === null || Array.isArray(schema)) {
    throw new Error(`${SCHEMA_PATH} is not a JSON Schema object`);
  }
  const source = generateZodModule(schema as Record<string, unknown>, {
    rootName: "CaseBundle",
    header: HEADER,
  });
  return format(source, { parser: "typescript", filepath: OUTPUT_PATH });
}

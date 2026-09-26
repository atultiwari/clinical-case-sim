// Writes src/generated/case-bundle.ts from the Case Library's bundle schema.
// Usage: pnpm --filter @nidana/contracts generate
import { writeFile } from "node:fs/promises";
import { OUTPUT_PATH, renderBundleModule } from "./render.ts";

try {
  await writeFile(OUTPUT_PATH, await renderBundleModule(), "utf8");
} catch (error) {
  console.error("Could not generate the bundle contracts:", error);
  process.exitCode = 1;
}

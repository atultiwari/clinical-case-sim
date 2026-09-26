import { readFileSync } from "node:fs";
import { expect, it } from "vitest";
import { ENGINE_VERSION } from "../src/index.ts";

it("matches the package version", () => {
  const pkg = JSON.parse(
    readFileSync(new URL("../package.json", import.meta.url), "utf8"),
  ) as { version: string };
  expect(ENGINE_VERSION).toBe(pkg.version);
});

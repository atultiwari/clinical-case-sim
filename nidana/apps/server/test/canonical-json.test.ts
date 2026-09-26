import { createHash } from "node:crypto";
import { readFileSync, readdirSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { canonicalJson, sha256Hex } from "@/lib/canonical-json";
import { EXPORTS_DIR } from "./helpers";

describe("canonicalJson (RFC 8785)", () => {
  it("sorts keys by UTF-16 code units and drops whitespace", () => {
    expect(canonicalJson({ b: 1, a: [true, null, "x"], "€": 0, A: {} })).toBe(
      '{"A":{},"a":[true,null,"x"],"b":1,"€":0}',
    );
  });

  it("writes numbers as ECMAScript does", () => {
    expect(canonicalJson([1e21, 0.1, -0, 77.8, 1.0])).toBe(
      "[1e+21,0.1,0,77.8,1]",
    );
  });

  it("refuses values JSON cannot hold", () => {
    expect(() => canonicalJson(Number.NaN)).toThrow(/finite/);
    expect(() => canonicalJson({ a: undefined })).toThrow(/undefined/);
  });

  it.each(readdirSync(EXPORTS_DIR).filter((n) => n.endsWith(".json")))(
    "reproduces %s byte for byte, so its SHA-256 checks out",
    (name) => {
      const bytes = readFileSync(`${EXPORTS_DIR}${name}`, "utf8");
      const expected = readFileSync(`${EXPORTS_DIR}${name}.sha256`, "utf8")
        .trim()
        .split(/\s+/)[0];
      expect(canonicalJson(JSON.parse(bytes))).toBe(bytes);
      expect(sha256Hex(canonicalJson(JSON.parse(bytes)))).toBe(expected);
      expect(createHash("sha256").update(bytes).digest("hex")).toBe(expected);
    },
  );
});

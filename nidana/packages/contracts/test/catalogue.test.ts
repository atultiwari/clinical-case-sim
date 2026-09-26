import { describe, expect, it } from "vitest";
import { parseCatalogue, parseCatalogueJson } from "../src/index.ts";
import { fixture } from "./helpers.ts";

type Json = Record<string, unknown>;

function withFirst(key: string, change: Json): Json {
  const catalogue = fixture("catalogue");
  const rows = (catalogue[key] as Json[]).map((row, i) =>
    i === 0 ? { ...row, ...change } : row,
  );
  return { ...catalogue, [key]: rows };
}

function errorOf(input: unknown): string {
  const result = parseCatalogue(input);
  if (result.success) throw new Error("expected the catalogue to be rejected");
  return result.error.message;
}

describe("parseCatalogue", () => {
  it("accepts the fixture export", () => {
    const input = fixture("catalogue");
    const result = parseCatalogue(input);
    expect(result.error).toBeNull();
    expect(result.data).toEqual(input);
  });

  it("rejects an id that does not fit its kind", () => {
    const message = errorOf(withFirst("items", { id: "LAB.HAEM.CBC" }));
    expect(message).toContain("Invalid catalogue export");
    expect(message).toContain("items[0].id");
    expect(message).toContain("diagnosis");
  });

  it("rejects an unknown item kind", () => {
    expect(errorOf(withFirst("items", { kind: "procedure" }))).toContain(
      "items[0].kind",
    );
  });

  it("rejects an unknown test route and a non-component in a test", () => {
    expect(
      errorOf(withFirst("tests", { route: "service.cardiology" })),
    ).toContain("tests[0].route");
    expect(errorOf(withFirst("tests", { components: ["LAB.X"] }))).toContain(
      "tests[0].components[0]",
    );
  });

  it("rejects an unknown sex in a reference range", () => {
    const component = (fixture("catalogue").components as Json[])[0] as Json;
    const ranges = [{ ...(component.ref_ranges as Json[])[0], sex: "X" }];
    const message = errorOf(withFirst("components", { ref_ranges: ranges }));
    expect(message).toContain("components[0].ref_ranges[0].sex");
  });

  it("rejects an unknown review status and value rule kind", () => {
    expect(
      errorOf(withFirst("normal_templates", { review_status: "draft" })),
    ).toContain("normal_templates[0].review_status");
    expect(errorOf(withFirst("value_rules", { kind: "product" }))).toContain(
      "value_rules[0].kind",
    );
  });

  it("reports text that is not JSON", () => {
    const result = parseCatalogueJson("[");
    expect(result.error?.message).toMatch(
      /^The catalogue export is not valid JSON/,
    );
    expect(
      parseCatalogueJson(JSON.stringify(fixture("catalogue"))).success,
    ).toBe(true);
  });
});

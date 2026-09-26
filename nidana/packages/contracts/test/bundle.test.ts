import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, expectTypeOf, it } from "vitest";
import {
  PINNED_BUNDLE_SCHEMA_VERSION,
  PINNED_CATALOGUE_VERSION,
  parseBundle,
  parseBundleJson,
  type CaseBundle,
  type Condition,
} from "../src/index.ts";
import { EXPORTS_DIR, exportedBundleFiles, fixture } from "./helpers.ts";

type Json = Record<string, unknown>;

function errorOf(input: unknown): string {
  const result = parseBundle(input);
  if (result.success) throw new Error("expected the bundle to be rejected");
  return result.error.message;
}

function list(bundle: Json, key: string): Json[] {
  return bundle[key] as Json[];
}

describe("parseBundle", () => {
  it("accepts the hand-made fixture and keeps every field", () => {
    const input = fixture("bundle");
    const result = parseBundle(input);
    expect(result.error).toBeNull();
    expect(result.success).toBe(true);
    expect(result.data).toEqual(input);
  });

  it("rejects a source without a licence, naming the field", () => {
    const bundle = fixture("bundle");
    const source = Object.fromEntries(
      Object.entries(bundle.source as Json).filter(
        ([key]) => key !== "licence",
      ),
    );
    const message = errorOf({ ...bundle, source });
    expect(message).toContain("Invalid case bundle");
    expect(message).toContain("source.licence");
    expect(message).toMatch(/expected string/);
  });

  it("rejects an unknown origin, naming the fact and the allowed origins", () => {
    const bundle = fixture("bundle");
    const facts = list(bundle, "facts").map((fact, i) =>
      i === 1 ? { ...fact, origin: "invented" } : fact,
    );
    const message = errorOf({ ...bundle, facts });
    expect(message).toContain("facts[1].origin");
    expect(message).toContain('"article"');
    expect(message).toContain('"derived"');
  });

  it("lists every problem, one per line", () => {
    const bundle = fixture("bundle");
    const result = parseBundle({
      ...bundle,
      schema_version: "0.2",
      catalogue_version: -1,
    });
    expect(result.success).toBe(false);
    expect(result.error?.issues.map((issue) => issue.path)).toEqual([
      "schema_version",
      "catalogue_version",
    ]);
    expect(result.error?.message).toContain("2 problems");
  });

  it("accepts a de novo case with no source", () => {
    expect(parseBundle({ ...fixture("bundle"), source: null }).success).toBe(
      true,
    );
  });

  it("rejects a malformed bundle id", () => {
    expect(errorOf({ ...fixture("bundle"), bundle_id: "PMC1@v1" })).toContain(
      "bundle_id",
    );
  });

  it("rejects a clock date that is not a calendar date", () => {
    const bundle = { ...fixture("bundle"), clock: { day_0: "13/07/2022" } };
    expect(errorOf(bundle)).toContain("clock.day_0");
  });

  it("requires a status line on an original report", () => {
    const bundle = fixture("bundle");
    const reports = list(bundle, "reports").map((report, i) =>
      i === 0 ? { ...report, status_line: null } : report,
    );
    const message = errorOf({ ...bundle, reports });
    expect(message).toContain("reports[0].status_line");
    expect(message).toContain('when variant is "original"');
  });

  it("keeps an original report provisional", () => {
    const bundle = fixture("bundle");
    const reports = list(bundle, "reports").map((report, i) =>
      i === 0 ? { ...report, status: "final" } : report,
    );
    expect(errorOf({ ...bundle, reports })).toContain("reports[0].status");
  });

  it("does not apply the original-report rule to other variants", () => {
    const bundle = fixture("bundle");
    const reports = list(bundle, "reports").map((report) => ({
      ...report,
      status_line: null,
    }));
    const withExpertOnly = { ...bundle, reports: reports.slice(1) };
    expect(parseBundle(withExpertOnly).success).toBe(true);
  });

  describe("scoring conditions", () => {
    function withMustDo(condition: unknown): Json {
      const bundle = fixture("bundle");
      const groundTruth = bundle.ground_truth as Json;
      return {
        ...bundle,
        ground_truth: {
          ...groundTruth,
          must_do: [{ text: "x", if: condition }],
        },
      };
    }

    it("accepts nested conditions", () => {
      const condition = {
        any: [{ not: { dx_in: ["DX.A"] } }, { all: [{ asked_any: ["HX.A"] }] }],
      };
      expect(parseBundle(withMustDo(condition)).success).toBe(true);
    });

    it("rejects an unknown condition keyword, pointing inside the scored item", () => {
      const message = errorOf(withMustDo({ asked_all: ["HX.A"] }));
      expect(message).toContain("ground_truth.must_do[0].if");
      expect(message).toContain("asked_all");
    });

    it("rejects an empty condition and one with three keywords", () => {
      expect(errorOf(withMustDo({}))).toContain("found 0");
      const three = {
        dx_in: ["DX.A"],
        asked_any: ["HX.A"],
        ordered_any: ["LAB.A"],
      };
      expect(errorOf(withMustDo(three))).toContain("found 3");
    });

    it("rejects from_tests without finding_released", () => {
      const message = errorOf(withMustDo({ from_tests: ["LAB.HAEM.FILM"] }));
      expect(message).toContain("ground_truth.must_do[0].if.finding_released");
      expect(message).toContain('required when "from_tests" is present');
    });

    it("reports a keyword count problem even when a keyword is also malformed", () => {
      const result = parseBundle(
        withMustDo({ dx_in: "DX.A", asked_any: ["HX.A"], plan_has: ["RX.A"] }),
      );
      const problems =
        result.error?.issues.map((issue) => issue.message).join("\n") ?? "";
      expect(problems).toContain("expected array");
      expect(problems).toContain("found 3");
    });

    it("reports a missing status line even when another report field is malformed", () => {
      const bundle = fixture("bundle");
      const reports = list(bundle, "reports").map((report, i) =>
        i === 0
          ? { ...report, status_line: null, findings: ["NOT.A.FINDING"] }
          : report,
      );
      const paths = parseBundle({ ...bundle, reports }).error?.issues.map(
        (issue) => issue.path,
      );
      expect(paths).toEqual([
        "reports[0].findings[0]",
        "reports[0].status_line",
      ]);
    });

    it("rejects an empty id list and a plan_before that is not a pair", () => {
      expect(errorOf(withMustDo({ dx_in: [] }))).toContain("dx_in");
      expect(errorOf(withMustDo({ plan_before: ["A"] }))).toContain(
        "plan_before",
      );
    });

    it("checks consult note conditions too", () => {
      const bundle = fixture("bundle");
      const notes = list(bundle, "consult_notes").map((note) => ({
        ...note,
        condition: {},
      }));
      expect(errorOf({ ...bundle, consult_notes: notes })).toContain(
        "consult_notes[0].condition",
      );
    });
  });

  it("types the recursive condition precisely", () => {
    expectTypeOf<Condition>().not.toBeAny();
    expectTypeOf<Condition["not"]>().toEqualTypeOf<Condition | undefined>();
    expectTypeOf<CaseBundle["schema_version"]>().toEqualTypeOf<"0.3">();
  });

  it("rejects input that is not an object", () => {
    expect(errorOf("a bundle")).toContain("expected object");
    expect(errorOf(null)).toContain("expected object");
  });
});

describe("parseBundleJson", () => {
  it("parses JSON text", () => {
    const text = JSON.stringify(fixture("bundle"));
    expect(parseBundleJson(text).success).toBe(true);
  });

  it("reports text that is not JSON", () => {
    const result = parseBundleJson("{ not json");
    expect(result.success).toBe(false);
    expect(result.error?.message).toMatch(/^The case bundle is not valid JSON/);
  });
});

describe("the Case Library's exported bundles", () => {
  const files = exportedBundleFiles();

  it("include the pilot on the pinned catalogue", () => {
    expect(files).toContain("PMC12949993@v1.r2.json");
  });

  it.each(files)("%s validates", (name) => {
    const result = parseBundleJson(
      readFileSync(join(EXPORTS_DIR, name), "utf8"),
    );
    expect(result.error?.message ?? null).toBeNull();
    expect(result.data?.schema_version).toBe(PINNED_BUNDLE_SCHEMA_VERSION);
    expect(`${result.data?.bundle_id}.json`).toBe(name);
  });

  it("are all on the pinned catalogue except the pilot's first revision", () => {
    const older = files.filter((name) => {
      const bundle = JSON.parse(
        readFileSync(join(EXPORTS_DIR, name), "utf8"),
      ) as Json;
      return bundle.catalogue_version !== PINNED_CATALOGUE_VERSION;
    });
    expect(older).toEqual(["PMC12949993@v1.r1.json"]);
  });
});

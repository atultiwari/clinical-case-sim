import type { MissingRequest } from "@nidana/contracts/api";
import { describe, expect, it } from "vitest";
import {
  MAX_MISSING_QUERY,
  createMissingReporter,
  missingQuery,
} from "../src/lib/missing";

/** N1.7: an unmatched search is reported once, with the encounter, kind and query only. */

const request = (query: string): MissingRequest => ({
  encounterId: "e1",
  kind: "test",
  query,
});

describe("missingQuery", () => {
  it("reports a search of two or more characters that found nothing", () => {
    expect(missingQuery("  hair   arsenic ", 0)).toBe("hair arsenic");
  });

  it("does not report a search that found something, or one too short to search", () => {
    expect(missingQuery("blood count", 3)).toBeNull();
    expect(missingQuery(" a ", 0)).toBeNull();
    expect(missingQuery("   ", 0)).toBeNull();
  });

  it("cuts a long query to the server's limit", () => {
    expect(missingQuery("x".repeat(500), 0)).toHaveLength(MAX_MISSING_QUERY);
  });
});

describe("createMissingReporter", () => {
  it("sends each query once per encounter and kind, ignoring case and spacing", async () => {
    const sent: MissingRequest[] = [];
    const report = createMissingReporter(async (r) => {
      sent.push(r);
    });
    report(request("Hair arsenic"));
    report(request("hair  ARSENIC"));
    report({ ...request("hair arsenic"), kind: "history" });
    report({ ...request("hair arsenic"), encounterId: "e2" });
    await Promise.resolve();
    expect(sent).toEqual([
      request("Hair arsenic"),
      { ...request("hair arsenic"), kind: "history" },
      { ...request("hair arsenic"), encounterId: "e2" },
    ]);
  });

  it("forgets a query whose report failed, so a later search can send it again", async () => {
    const sent: string[] = [];
    let fail = true;
    const failures: unknown[] = [];
    const report = createMissingReporter(
      async (r) => {
        sent.push(r.query);
        if (fail) throw new Error("offline");
      },
      (e) => failures.push(e),
    );
    report(request("serum zinc"));
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(failures).toHaveLength(1);
    fail = false;
    report(request("serum zinc"));
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(sent).toEqual(["serum zinc", "serum zinc"]);
  });
});

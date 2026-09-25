import { describe, expect, it } from "vitest";

import { caseHref, parseCaseVersionId } from "@/lib/case-id";
import { describeDatabaseHost } from "@/lib/db-host";
import { groupBy } from "@/lib/group";
import { firstParam, pageNumber, toQueryString } from "@/lib/search-params";

describe("case version ids", () => {
  it("accepts encoded and plain ids", () => {
    expect(parseCaseVersionId("PMC12949993%40v1")).toBe("PMC12949993@v1");
    expect(parseCaseVersionId("NID-0001@v2")).toBe("NID-0001@v2");
  });

  it("rejects anything else", () => {
    expect(parseCaseVersionId("PMC1")).toBeNull();
    expect(parseCaseVersionId("PMC1@v1'; drop table x")).toBeNull();
    expect(parseCaseVersionId("%E0%A4%A")).toBeNull();
  });

  it("builds tab links", () => {
    expect(caseHref("PMC1@v1")).toBe("/cases/PMC1%40v1");
    expect(caseHref("PMC1@v1", "facts")).toBe("/cases/PMC1%40v1/facts");
  });
});

describe("describeDatabaseHost", () => {
  it("shows host, port and database without credentials", () => {
    const host = describeDatabaseHost("postgresql://postgres:secret@127.0.0.1:55322/postgres");
    expect(host).toEqual({ host: "127.0.0.1", port: "55322", database: "postgres", local: true });
    expect(JSON.stringify(host)).not.toContain("secret");
  });

  it("marks a pooler host as cloud", () => {
    expect(
      describeDatabaseHost("postgresql://studio_reader.ref:pw@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres"),
    ).toMatchObject({ host: "aws-0-ap-northeast-1.pooler.supabase.com", local: false });
  });

  it("rejects non-Postgres or broken URLs", () => {
    expect(describeDatabaseHost("https://example.com")).toBeNull();
    expect(describeDatabaseHost("not a url")).toBeNull();
  });
});

describe("groupBy", () => {
  it("keeps first-seen order", () => {
    expect(groupBy(["b1", "a1", "b2"], (s) => s[0] ?? "")).toEqual([
      { key: "b", rows: ["b1", "b2"] },
      { key: "a", rows: ["a1"] },
    ]);
  });
});

describe("search params", () => {
  it("reads the first non-empty value", () => {
    expect(firstParam({ a: ["x", "y"] }, "a")).toBe("x");
    expect(firstParam({ a: "  " }, "a")).toBeUndefined();
  });

  it("parses page numbers safely", () => {
    expect(pageNumber("7")).toBe(7);
    expect(pageNumber("abc")).toBe(1);
    expect(pageNumber("99999999")).toBe(10000);
  });

  it("builds query strings from defined values", () => {
    expect(toQueryString({ a: "1", b: undefined, c: "" })).toBe("?a=1");
    expect(toQueryString({})).toBe("");
  });
});

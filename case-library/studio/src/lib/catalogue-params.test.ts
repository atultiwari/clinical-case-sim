import { describe, expect, it } from "vitest";

import { catalogueQuery, containsPattern, pageCount, parseCatalogueParams } from "@/lib/catalogue-params";

describe("parseCatalogueParams", () => {
  it("reads view, kind, search and page", () => {
    expect(parseCatalogueParams({ view: "components", kind: "test", q: " haem ", page: "2" })).toEqual({
      view: "components",
      kind: "test",
      q: "haem",
      page: 2,
    });
  });

  it("falls back to items, all kinds, page 1", () => {
    expect(parseCatalogueParams({ view: "x", kind: "drug" })).toEqual({ view: "items", kind: undefined, q: undefined, page: 1 });
  });
});

describe("catalogueQuery", () => {
  it("drops the kind in the components view and resets the page", () => {
    const params = parseCatalogueParams({ kind: "test", q: "lead", page: "3" });
    expect(catalogueQuery(params, { view: "components" })).toBe("?view=components&q=lead");
    expect(catalogueQuery(params, { page: 4 })).toBe("?kind=test&q=lead&page=4");
  });
});

describe("containsPattern", () => {
  it("escapes LIKE wildcards", () => {
    expect(containsPattern("50%_a\\b")).toBe("%50\\%\\_a\\\\b%");
  });
});

describe("pageCount", () => {
  it("is at least one", () => {
    expect(pageCount(0, 50)).toBe(1);
    expect(pageCount(101, 50)).toBe(3);
  });
});

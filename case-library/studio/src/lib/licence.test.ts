import { describe, expect, it } from "vitest";

import { hasNcOrNd, licenceBadges } from "@/lib/licence";

const labels = (flags: Parameters<typeof licenceBadges>[0]) => licenceBadges(flags).map((b) => b.label);

describe("hasNcOrNd", () => {
  it.each([
    ["CC BY-NC 4.0", true],
    ["CC BY-NC-ND 4.0", true],
    ["CC BY-ND 4.0", true],
    ["cc by-nc-sa 4.0", true],
    ["CC BY 4.0", false],
    ["CC BY-SA 4.0", false],
    ["CC0 1.0", false],
    [null, false],
  ])("%s -> %s", (licence, expected) => {
    expect(hasNcOrNd(licence)).toBe(expected);
  });
});

describe("licenceBadges", () => {
  it("marks a CC BY case for production and public release", () => {
    expect(labels({ licence: "CC BY 4.0", production_ok: true, public_release_ok: true })).toEqual([
      "Production",
      "Public release",
    ]);
  });

  it("shows a red Development only badge when production_ok is false", () => {
    const badges = licenceBadges({ licence: "CC BY-NC 4.0", production_ok: false, public_release_ok: true });
    expect(badges[0]).toMatchObject({ label: "Development only", tone: "danger" });
    expect(badges.map((b) => b.label)).toContain("Public release");
  });

  it("treats missing flags as development only", () => {
    expect(labels({ licence: null, production_ok: null, public_release_ok: null })).toEqual(["Development only"]);
  });

  it("flags an NC or ND licence marked production_ok", () => {
    expect(labels({ licence: "CC BY-ND 4.0", production_ok: true, public_release_ok: false })).toEqual([
      "Production",
      "Check flags",
    ]);
  });
});

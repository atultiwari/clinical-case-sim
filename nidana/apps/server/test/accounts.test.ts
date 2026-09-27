import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { canonicalJson, sha256Hex } from "@/lib/canonical-json";
import { createBundleRegistry } from "@/lib/registry";
import {
  ATTRIBUTION_STATEMENT,
  commit,
  credits,
  getMe,
  listCases,
  listMyEncounters,
  saveMe,
  startEncounter,
  type GameDeps,
} from "@/lib/game";
import type { BundleSource } from "@/lib/bundles";
import { EXPORTS_DIR, PILOT, catalogue, deps } from "./helpers";

const A = {
  playerId: "aaaaaaaa-1111-4111-8111-111111111111",
  role: "player" as const,
};
const B = {
  playerId: "bbbbbbbb-2222-4222-8222-222222222222",
  role: "player" as const,
};
const ADMIN = {
  playerId: "cccccccc-3333-4333-8333-333333333333",
  role: "admin" as const,
};
const PROFILE = {
  nickname: "Night owl",
  trainingLevel: "resident",
  consentResearch: false,
  agreed: true,
};
const PILOT_SLUG = "c-6gizm";

function unwrap<T>(
  outcome:
    | { ok: true; data: T }
    | { ok: false; error: { code: string; message: string } },
): T {
  if (!outcome.ok)
    throw new Error(`${outcome.error.code}: ${outcome.error.message}`);
  return outcome.data;
}

describe("consent and the profile", () => {
  it("refuses play before the player has agreed", async () => {
    const game = deps();
    const outcome = await startEncounter(game, A, {
      slug: PILOT_SLUG,
      difficulty: "standard",
    });
    expect(outcome.ok ? null : outcome.error).toMatchObject({
      status: 403,
      code: "consent_required",
    });
    expect((await getMe(game, A)).ok).toBe(false);
  });

  it("creates the profile on consent, with research consent off unless chosen", async () => {
    const game = deps();
    const profile = unwrap(await saveMe(game, A, PROFILE));
    expect(profile).toMatchObject({
      nickname: "Night owl",
      trainingLevel: "resident",
      consentResearch: false,
      role: "player",
    });
    expect(unwrap(await getMe(game, A))).toEqual(profile);
  });

  it("updates the nickname and withdraws research consent without moving the join date", async () => {
    const game = {
      ...deps(),
      now: (() => {
        let t = 0;
        return () => new Date(Date.UTC(2026, 8, 27, 0, t++));
      })(),
    } as GameDeps;
    const first = unwrap(
      await saveMe(game, A, { ...PROFILE, consentResearch: true }),
    );
    const second = unwrap(
      await saveMe(game, A, {
        ...PROFILE,
        nickname: "Early bird",
        consentResearch: false,
      }),
    );
    expect(second).toMatchObject({
      nickname: "Early bird",
      consentResearch: false,
      joinedAt: first.joinedAt,
    });
  });

  it.each([
    [{ ...PROFILE, agreed: false }, "agreed"],
    [{ ...PROFILE, nickname: "a" }, "nickname"],
    [{ ...PROFILE, nickname: "someone@example.org" }, "nickname"],
    [{ ...PROFILE, trainingLevel: "professor" }, "trainingLevel"],
    [{ ...PROFILE, email: "x@y.z" }, "email"],
  ])("refuses %j", async (body, field) => {
    const outcome = await saveMe(deps(), A, body);
    expect(outcome.ok ? null : outcome.error).toMatchObject({ status: 400 });
    expect(outcome.ok ? "" : outcome.error.message).toContain(field);
  });
});

describe("each player sees only their own encounters", () => {
  it("lists a player's encounters, newest first, with scores once committed", async () => {
    let minute = 0;
    const game = {
      ...deps(),
      now: () => new Date(Date.UTC(2026, 8, 27, 9, minute++)),
    } as GameDeps;
    await saveMe(game, A, PROFILE);
    await saveMe(game, B, { ...PROFILE, nickname: "Other" });
    const first = unwrap(
      await startEncounter(game, A, {
        slug: PILOT_SLUG,
        difficulty: "standard",
      }),
    );
    const second = unwrap(
      await startEncounter(game, A, { slug: PILOT_SLUG, difficulty: "guided" }),
    );
    const theirs = unwrap(
      await startEncounter(game, B, { slug: PILOT_SLUG, difficulty: "expert" }),
    );
    await commit(game, A.playerId, first.encounterId, {
      dx: "DX.LEAD_POISONING",
      evidence: [],
      plan: [],
    });

    const mine = unwrap(await listMyEncounters(game, A));
    expect(mine.map((e) => e.encounterId)).toEqual([
      second.encounterId,
      first.encounterId,
    ]);
    expect(mine[1]).toMatchObject({
      status: "committed",
      caseSlug: PILOT_SLUG,
      total: expect.any(Number),
    });
    expect(mine.map((e) => e.encounterId)).not.toContain(theirs.encounterId);
    expect(
      unwrap(await listMyEncounters(game, B)).map((e) => e.encounterId),
    ).toEqual([theirs.encounterId]);
    expect(JSON.stringify(mine)).not.toContain(PILOT);
  });
});

describe("roles and licences (S-006)", () => {
  /** The pilot relabelled as a no-derivatives case, to check who may see such cases. */
  function withNdCase(): GameDeps {
    const body = JSON.parse(
      readFileSync(`${EXPORTS_DIR}${PILOT}.json`, "utf8"),
    ) as { source: Record<string, unknown> };
    const text = canonicalJson({
      ...body,
      source: { ...body.source, licence: "CC BY-NC-ND 4.0" },
    });
    const source: BundleSource = {
      listPublished: async () => [PILOT],
      read: async (id) =>
        id === PILOT ? { id, text, sha256: sha256Hex(text) } : null,
    };
    return deps({ registry: createBundleRegistry(source, catalogue) });
  }

  it("shows ND cases to admins only, and lets only admins start them", async () => {
    const game = withNdCase();
    expect(unwrap(await listCases(game, A))).toEqual([]);
    expect(unwrap(await listCases(game, ADMIN)).map((c) => c.slug)).toEqual([
      PILOT_SLUG,
    ]);
    await saveMe(game, A, PROFILE);
    await saveMe(game, ADMIN, PROFILE);
    const refused = await startEncounter(game, A, {
      slug: PILOT_SLUG,
      difficulty: "standard",
    });
    expect(refused.ok ? null : refused.error.code).toBe("not_found");
    expect(
      (
        await startEncounter(game, ADMIN, {
          slug: PILOT_SLUG,
          difficulty: "standard",
        })
      ).ok,
    ).toBe(true);
    expect(unwrap(await credits(game, A)).sources).toEqual([]);
  });

  it("reports the admin role in the profile", async () => {
    const game = deps();
    expect(unwrap(await saveMe(game, ADMIN, PROFILE)).role).toBe("admin");
  });
});

describe("credits", () => {
  it("lists every visible case's attribution, sorted, with the general statement", async () => {
    const result = unwrap(await credits(deps(), A));
    expect(result.statement).toBe(ATTRIBUTION_STATEMENT);
    expect(result.sources).toHaveLength(10);
    expect(result.sources.every((s) => s.licence.startsWith("CC"))).toBe(true);
    const citations = result.sources.map((s) => s.citation ?? "");
    expect(citations).toEqual(
      [...citations].sort((a, b) => a.localeCompare(b)),
    );
  });
});

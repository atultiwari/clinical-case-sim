import fc from "fast-check";
import { describe, expect, it } from "vitest";
import type { Action } from "@nidana/engine";
import {
  act,
  commit,
  getDebrief,
  getView,
  listCases,
  logMissing,
  startEncounter,
  type GameDeps,
} from "@/lib/game";
import type { PlayerView } from "@/lib/view";
import { scanForLeaks } from "./leak-scan";
import {
  PILOT,
  benchmarkActions,
  catalogue,
  deps,
  pilot,
  registry,
} from "./helpers";

const PLAYER = "11111111-1111-4111-8111-111111111111";
const OTHER = "22222222-2222-4222-8222-222222222222";

async function pilotSlug(): Promise<string> {
  return (await pilot()).bundle.case.slug ?? "";
}

function unwrap<T>(
  outcome:
    | { ok: true; data: T }
    | { ok: false; error: { code: string; message: string } },
): T {
  if (!outcome.ok)
    throw new Error(`${outcome.error.code}: ${outcome.error.message}`);
  return outcome.data;
}

async function start(
  game: GameDeps,
  difficulty = "standard",
): Promise<PlayerView> {
  return unwrap(
    await startEncounter(game, PLAYER, { slug: await pilotSlug(), difficulty }),
  );
}

/** Plays actions through the service and returns every response. */
async function playAll(
  game: GameDeps,
  id: string,
  actions: readonly Action[],
): Promise<unknown[]> {
  const responses: unknown[] = [];
  for (const action of actions) {
    const outcome = await act(game, PLAYER, id, action);
    responses.push(outcome.ok ? outcome.data : outcome.error);
  }
  return responses;
}

const refFor = (
  view: PlayerView,
  predicate: (e: PlayerView["chart"][number]) => boolean,
): string => view.chart.find(predicate)?.ref ?? "missing";

describe("leak tests (SPEC §6.4)", () => {
  it("no response on the benchmark path leaks before the debrief", async () => {
    const game = deps();
    const started = await start(game);
    const responses = [
      started,
      unwrap(await listCases(game)),
      ...(await playAll(game, started.encounterId, benchmarkActions())),
      unwrap(await getView(game, PLAYER, started.encounterId)),
    ];
    const prepared = await pilot();
    expect(responses.flatMap((r) => scanForLeaks(prepared, r))).toEqual([]);
  });

  it("no response leaks in Guided mode or on random action sequences", async () => {
    const prepared = await pilot();
    const items = (kind: string) =>
      catalogue.items
        .filter(
          (i) => i.kind === kind && i.specialty_scope.includes("attending"),
        )
        .map((i) => i.id);
    const anyAction = fc.oneof(
      fc
        .constantFrom(...items("history"))
        .map((item) => ({ kind: "ask", item }) as Action),
      fc
        .constantFrom(...items("exam"))
        .map((item) => ({ kind: "examine", item }) as Action),
      fc
        .constantFrom(...items("test"))
        .map((item) => ({ kind: "order", item }) as Action),
      fc
        .constantFrom(...items("referral"))
        .map((item) => ({ kind: "refer", item }) as Action),
      fc.constant({ kind: "wait" } as Action),
    );
    await fc.assert(
      fc.asyncProperty(
        fc.array(anyAction, { maxLength: 30 }),
        fc.constantFrom("guided", "standard", "expert"),
        async (actions, difficulty) => {
          const game = deps();
          const started = await start(game, difficulty);
          const responses = await playAll(game, started.encounterId, [
            ...actions,
            { kind: "wait", minutes: 3000 },
          ]);
          const leaks = [started, ...responses].flatMap((r) =>
            scanForLeaks(prepared, r),
          );
          expect(leaks).toEqual([]);
        },
      ),
      { numRuns: 40, seed: 42 },
    );
  });

  it("the scan itself catches a leak", async () => {
    const prepared = await pilot();
    expect(
      scanForLeaks(prepared, { chart: [{ origin: "affected", text: "H10" }] }),
    ).toHaveLength(2);
    expect(
      scanForLeaks(prepared, { note: "Consistent with lead poisoning" }),
    ).toHaveLength(1);
    expect(
      scanForLeaks(prepared, { differential: [{ items: ["lead poisoning"] }] }),
    ).toEqual([]);
    expect(scanForLeaks(prepared, { x: PILOT })).toHaveLength(1);
  });
});

describe("encounters", () => {
  it("starts on the newest revision and hides which one", async () => {
    const game = deps();
    const view = await start(game);
    expect(view.status).toBe("active");
    expect(view.chart.map((e) => e.kind)).toEqual([
      "vignette",
      "vignette",
      "vignette",
      "vignette",
    ]);
    expect((await game.store.get(view.encounterId))?.bundleId).toBe(PILOT);
  });

  it("refuses an unknown case, a bad difficulty and a malformed action", async () => {
    const game = deps();
    expect(
      (
        await startEncounter(game, PLAYER, {
          slug: "c-zzzzz",
          difficulty: "standard",
        })
      ).ok,
    ).toBe(false);
    const bad = await startEncounter(game, PLAYER, {
      slug: await pilotSlug(),
      difficulty: "easy",
    });
    expect(bad.ok ? 0 : bad.error.status).toBe(400);
    const view = await start(game);
    const malformed = await act(game, PLAYER, view.encounterId, {
      kind: "shout",
    });
    expect(malformed.ok ? 0 : malformed.error.status).toBe(400);
    const commitHere = await act(game, PLAYER, view.encounterId, {
      kind: "commit",
      dx: "DX.X",
      evidence: [],
      plan: [],
    });
    expect(commitHere.ok ? 0 : commitHere.error.status).toBe(400);
  });

  it("returns an engine refusal as 422 with its code", async () => {
    const game = deps();
    const view = await start(game);
    const refused = await act(game, PLAYER, view.encounterId, {
      kind: "ask",
      item: "HX.NOPE",
    });
    expect(refused.ok ? null : refused.error).toMatchObject({
      status: 422,
      code: "unknown_item",
    });
  });

  it("shows another player's encounter as missing", async () => {
    const game = deps();
    const view = await start(game);
    for (const outcome of [
      await getView(game, OTHER, view.encounterId),
      await act(game, OTHER, view.encounterId, { kind: "wait" }),
      await getDebrief(game, OTHER, view.encounterId),
      await logMissing(game, OTHER, {
        encounterId: view.encounterId,
        kind: "test",
        query: "x",
      }),
    ]) {
      expect(outcome.ok ? null : outcome.error).toMatchObject({
        status: 404,
        code: "not_found",
      });
    }
  });

  it("marks a carried-forward result with the day it was taken", async () => {
    const game = deps();
    const view = await start(game);
    await playAll(game, view.encounterId, [
      { kind: "wait", minutes: 3 * 1440 },
      { kind: "order", item: "LAB.CHEM.FERRITIN" },
    ]);
    const after = unwrap(
      await act(game, PLAYER, view.encounterId, { kind: "wait" }),
    );
    const ferritin = after.chart.find(
      (e) => e.component?.id === "CMP.FERRITIN",
    );
    expect(ferritin).toMatchObject({
      kind: "result",
      requestedDay: 3,
      takenDay: 0,
    });
  });

  it("shows the provisional badge data for the first film in Standard", async () => {
    const game = deps();
    const view = await start(game);
    await act(game, PLAYER, view.encounterId, {
      kind: "order",
      item: "LAB.HAEM.FILM",
    });
    const after = unwrap(
      await act(game, PLAYER, view.encounterId, { kind: "wait" }),
    );
    expect(after.chart.find((e) => e.kind === "report")?.report).toMatchObject({
      status: "provisional",
      statusLine: expect.stringMatching(/^Provisional report/),
    });
  });

  it("reports a race on the action log as a conflict", async () => {
    const game = deps();
    const view = await start(game);
    const racing: GameDeps = {
      ...game,
      store: { ...game.store, append: async () => false },
    };
    const outcome = await act(racing, PLAYER, view.encounterId, {
      kind: "wait",
    });
    expect(outcome.ok ? null : outcome.error).toMatchObject({
      status: 409,
      code: "conflict",
    });
  });
});

describe("commit and debrief", () => {
  async function playedBenchmark(game: GameDeps): Promise<PlayerView> {
    const started = await start(game);
    await playAll(game, started.encounterId, benchmarkActions());
    return unwrap(await getView(game, PLAYER, started.encounterId));
  }

  const PLAN = [
    "ACT.STOP_SUSPECTED_SOURCE",
    "RX.CHELATION.SUCCIMER_ORAL",
    "ACT.NOTIFY_PUBLIC_HEALTH",
    "ACT.REPEAT_BLOOD_LEAD",
  ];

  it("maps chart references to evidence and scores the commit", async () => {
    const game = deps();
    const view = await playedBenchmark(game);
    const supplement = refFor(view, (e) => e.item === "HX.MEDS.SUPPLEMENTS");
    const lead = refFor(view, (e) => e.component?.id === "CMP.PB_BLOOD");
    const result = unwrap(
      await commit(game, PLAYER, view.encounterId, {
        dx: "DX.LEAD_POISONING",
        evidence: [supplement, lead],
        plan: PLAN,
      }),
    );
    expect(result.diagnosisAnchor).toBe(5);
    expect((await game.store.score(view.encounterId))?.engineVersion).toBe(
      "0.1.0",
    );
    expect((await game.store.get(view.encounterId))?.status).toBe("committed");
    const closed = await act(game, PLAYER, view.encounterId, { kind: "wait" });
    expect(closed.ok ? null : closed.error.code).toBe("committed");
  });

  it("refuses a reference that is not in the Chart", async () => {
    const game = deps();
    const view = await playedBenchmark(game);
    for (const ref of ["c9999", "H10"]) {
      const outcome = await commit(game, PLAYER, view.encounterId, {
        dx: "DX.LEAD_POISONING",
        evidence: [ref],
        plan: [],
      });
      expect(outcome.ok ? null : outcome.error.status).toBe(
        ref === "H10" ? 400 : 422,
      );
    }
  });

  it("opens the debrief only after the commit", async () => {
    const game = deps();
    const view = await playedBenchmark(game);
    const early = await getDebrief(game, PLAYER, view.encounterId);
    expect(early.ok ? null : early.error).toMatchObject({
      status: 409,
      code: "not_committed",
    });
    await commit(game, PLAYER, view.encounterId, {
      dx: "DX.LEAD_POISONING",
      evidence: [],
      plan: PLAN,
    });
    const debrief = unwrap(await getDebrief(game, PLAYER, view.encounterId));
    expect(debrief.bundleId).toBe(PILOT);
    expect(debrief.attribution?.licence).toBe("CC BY 4.0");
  });

  it("reports a failed store commit as a conflict", async () => {
    const game = deps();
    const view = await playedBenchmark(game);
    const racing: GameDeps = {
      ...game,
      store: { ...game.store, commit: async () => false },
    };
    const outcome = await commit(racing, PLAYER, view.encounterId, {
      dx: "DX.LEAD_POISONING",
      evidence: [],
      plan: [],
    });
    expect(outcome.ok ? null : outcome.error.code).toBe("conflict");
  });
});

describe("missing requests", () => {
  it("logs the bundle, kind and query and nothing that identifies the player", async () => {
    const game = deps();
    const view = await start(game);
    unwrap(
      await logMissing(game, PLAYER, {
        encounterId: view.encounterId,
        kind: "test",
        query: "  serum zinc  ",
      }),
    );
    expect(game.store.missing).toEqual([
      { bundleId: PILOT, kind: "test", query: "serum zinc" },
    ]);
    expect(JSON.stringify(game.store.missing)).not.toContain(PLAYER);
    expect(
      (
        await logMissing(game, PLAYER, {
          encounterId: view.encounterId,
          kind: "test",
          query: "",
        })
      ).ok,
    ).toBe(false);
  });
});

describe("a case whose bundle is later refused", () => {
  it("is reported as unavailable, not as an error", async () => {
    const game = deps();
    const view = await start(game);
    const broken: GameDeps = {
      ...game,
      registry: {
        ...registry,
        load: async () =>
          Promise.reject(
            new (await import("@/lib/bundles")).BundleRefusedError(
              "hash_mismatch",
              "x",
            ),
          ),
      },
    };
    const outcome = await getView(broken, PLAYER, view.encounterId);
    expect(outcome.ok ? null : outcome.error).toMatchObject({
      status: 503,
      code: "case_unavailable",
    });
  });
});

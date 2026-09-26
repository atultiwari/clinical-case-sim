import { describe, expect, it } from "vitest";
import { replay } from "@nidana/engine";
import { createRateLimiter } from "@/lib/rate-limit";
import { memoryStore } from "@/lib/store";
import { buildPlayerView, sourceOfRef } from "@/lib/view";
import { respond, withPlayer } from "@/lib/http";
import type { ServerContext } from "@/lib/context";
import { deps, pilot, settings } from "./helpers";

describe("the PlayerView", () => {
  it("shows qualitative results as text and marks a missing answer as no record", async () => {
    const prepared = await pilot();
    const qualitative = prepared.bundle.ledger.find(
      (r) => r.target.startsWith("CMP.") && r.value.value === undefined,
    );
    const test = prepared.catalogue.tests.find((t) =>
      t.components.includes(qualitative?.target ?? ""),
    );
    const state = replay(prepared, settings, "guided", [
      { kind: "order", item: test?.item_id ?? "" },
      { kind: "wait", minutes: 5000 },
    ]);
    const view = buildPlayerView(prepared, state, "e1");
    const entry = view.chart.find(
      (e) => e.component?.id === qualitative?.target,
    );
    expect(entry?.value).toBeNull();
    expect(typeof entry?.text).toBe("string");

    const broken = {
      ...prepared,
      factsByItem: new Map(),
      ledgerByTarget: new Map(),
    };
    const none = buildPlayerView(
      broken,
      replay(broken, settings, "standard", [
        { kind: "ask", item: "HX.MEDS.CURRENT" },
      ]),
      "e2",
    );
    expect(none.chart.at(-1)).toMatchObject({ kind: "no_record", text: null });
    expect(
      sourceOfRef(
        replay(broken, settings, "standard", [
          { kind: "ask", item: "HX.MEDS.CURRENT" },
        ]),
        "c4",
      ),
    ).toBeNull();
  });

  it("shows the conventional unit where the catalogue has one", async () => {
    const prepared = await pilot();
    const state = replay(prepared, settings, "standard", [
      { kind: "order", item: "LAB.HAEM.CBC" },
      { kind: "wait" },
    ]);
    const hb = buildPlayerView(prepared, state, "e3").chart.find(
      (e) => e.component?.id === "CMP.HB",
    );
    expect(hb?.value?.conventional).toEqual({
      unit: "g/dL",
      factor: 0.1,
      decimals: 0,
    });
  });
});

describe("the memory store", () => {
  it("refuses an encounter for an unknown player and a commit of a closed encounter", async () => {
    const store = memoryStore();
    const record = {
      id: "e",
      playerId: "p",
      bundleId: "b",
      difficulty: "standard" as const,
      status: "active" as const,
      startedAt: new Date(),
      endedAt: null,
    };
    await expect(store.create(record)).rejects.toThrow(/unknown player/);
    expect(
      await store.commit("nope", 0, { kind: "wait" }, {} as never, new Date()),
    ).toBe(false);
    expect(await store.get("nope")).toBeNull();
    expect(await store.actions("nope")).toEqual([]);
    expect(await store.score("nope")).toBeNull();
  });
});

describe("withPlayer", () => {
  const context = (overrides: Partial<ServerContext> = {}): ServerContext =>
    ({
      verifier: { verify: async () => ({ playerId: "p" }) },
      limits: {
        actions: createRateLimiter(1, 60_000),
        starts: createRateLimiter(1, 60_000),
        reads: createRateLimiter(1, 60_000),
      },
      game: deps(),
      catalogue: {} as never,
      ...overrides,
    }) as ServerContext;
  const request = new Request("http://x/api", {
    headers: { authorization: "Bearer t" },
  });

  it("rate-limits per player", async () => {
    const ctx = context();
    const ok = await withPlayer(
      request,
      "reads",
      async () => respond({ ok: true, data: 1 }),
      async () => ctx,
    );
    const limited = await withPlayer(
      request,
      "reads",
      async () => respond({ ok: true, data: 1 }),
      async () => ctx,
    );
    expect([ok.status, limited.status]).toEqual([200, 429]);
  });

  it("turns an unexpected error into a 500 without detail", async () => {
    const original = console.error;
    console.error = () => undefined;
    try {
      const response = await withPlayer(
        request,
        "reads",
        async () => {
          throw new Error("secret detail");
        },
        async () => context(),
      );
      expect(response.status).toBe(500);
      expect(await response.text()).not.toContain("secret detail");
    } finally {
      console.error = original;
    }
  });
});

describe("readJsonBody", () => {
  it("refuses an oversized body by its declared length without reading it", async () => {
    const { readJsonBody } = await import("@/lib/http");
    const request = new Request("http://x/api", {
      method: "POST",
      headers: { "content-length": "999999" },
      body: "{}",
    });
    const result = await readJsonBody(request);
    expect(result.ok ? 0 : result.response.status).toBe(413);
  });
});

describe("createRateLimiter", () => {
  it("forgets old windows when many keys pile up", () => {
    let now = 0;
    const limiter = createRateLimiter(1, 10, () => now);
    for (let i = 0; i <= 10_001; i += 1) limiter.take(`k${i}`);
    now = 100;
    expect(limiter.take("k0")).toBe(true);
  });
});

describe("CORS", () => {
  it("allows only listed origins, on replies and preflights", async () => {
    const { allowedOrigins, preflight, withCors } = await import("@/lib/http");
    const allowed = allowedOrigins({
      NIDANA_ALLOWED_ORIGINS: "http://localhost:8081, https://play.example.org",
    });
    const from = (origin: string) =>
      new Request("http://x/api", { headers: { origin } });
    const ok = preflight(from("http://localhost:8081"), allowed);
    expect(ok.status).toBe(204);
    expect(ok.headers.get("access-control-allow-origin")).toBe(
      "http://localhost:8081",
    );
    expect(ok.headers.get("access-control-allow-headers")).toContain(
      "authorization",
    );
    const other = withCors(
      from("https://evil.example"),
      new Response("x"),
      allowed,
    );
    expect(other.headers.get("access-control-allow-origin")).toBeNull();
    expect(other.headers.get("vary")).toBe("Origin");
    expect(allowedOrigins({}).size).toBe(0);
  });
});

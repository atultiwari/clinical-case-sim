import { beforeAll, describe, expect, it, vi } from "vitest";
import type { DebriefView } from "@nidana/contracts";
import type { SearchItem } from "@/lib/catalogue";
import type { CommitResult } from "@/lib/game";
import type { Envelope } from "@/lib/http";
import type { CaseCard } from "@/lib/registry";
import type { PlayerView } from "@/lib/view";
import { SECRET, tokenFor } from "./helpers";
import { NIDANA_DIR } from "./helpers";
import { scanForLeaks } from "./leak-scan";
import { pilot } from "./helpers";

const PLAYER = "33333333-3333-4333-8333-333333333333";

vi.stubEnv("SUPABASE_JWT_SECRET", SECRET);
vi.stubEnv("SUPABASE_URL", "http://127.0.0.1:55321");
vi.stubEnv("NIDANA_CONFIG_DIR", `${NIDANA_DIR}configs`);
vi.stubEnv(
  "NIDANA_CATALOGUE_PATH",
  `${NIDANA_DIR}conformance/catalogue/catalogue.v2.json`,
);
vi.stubEnv("NIDANA_EXPORTS_DIR", `${NIDANA_DIR}../case-library/exports`);

let auth: string;
beforeAll(async () => {
  const { SignJWT } = await import("jose");
  auth = `Bearer ${await new SignJWT({})
    .setProtectedHeader({ alg: "HS256" })
    .setSubject(PLAYER)
    .setAudience("authenticated")
    .setIssuer("http://127.0.0.1:55321/auth/v1")
    .setExpirationTime("1h")
    .sign(new TextEncoder().encode(SECRET))}`;
});

const req = (
  method: string,
  body?: unknown,
  authorization: string | null = auth,
): Request =>
  new Request("http://localhost/api", {
    method,
    headers: authorization === null ? {} : { authorization },
    ...(body === undefined
      ? {}
      : { body: typeof body === "string" ? body : JSON.stringify(body) }),
  });

const params = (id: string) => ({ params: Promise.resolve({ id }) });

async function json<T = unknown>(
  response: Response,
): Promise<{ status: number; body: Envelope<T> }> {
  return {
    status: response.status,
    body: (await response.json()) as Envelope<T>,
  };
}

describe("the API over HTTP", () => {
  it("refuses a request without a valid sign-in", async () => {
    const cases = await import("@/app/api/cases/route");
    expect(
      (await json(await cases.GET(req("GET", undefined, null)))).status,
    ).toBe(401);
    const bad = await tokenFor(PLAYER, "x".repeat(40));
    expect(
      (await json(await cases.GET(req("GET", undefined, `Bearer ${bad}`)))).body
        .error?.code,
    ).toBe("unauthorised");
  });

  it("plays an encounter end to end with no leak before the debrief", async () => {
    const prepared = await pilot();
    const cases = await import("@/app/api/cases/route");
    const catalogue = await import("@/app/api/catalogue/route");
    const start = await import("@/app/api/encounters/route");
    const actions = await import("@/app/api/encounters/[id]/actions/route");
    const view = await import("@/app/api/encounters/[id]/view/route");
    const commit = await import("@/app/api/encounters/[id]/commit/route");
    const debrief = await import("@/app/api/encounters/[id]/debrief/route");
    const missing = await import("@/app/api/missing/route");

    const list = await json<CaseCard[]>(await cases.GET(req("GET")));
    expect(list.body.success).toBe(true);
    const slug = prepared.bundle.case.slug;
    expect((list.body.data ?? []).map((c) => c.slug)).toContain(slug);

    const search = await json<SearchItem[]>(await catalogue.GET(req("GET")));
    expect(
      (search.body.data ?? []).find((i) => i.id === "LAB.HAEM.CBC"),
    ).toMatchObject({ priceInr: 300 });

    const me = await import("@/app/api/me/route");
    expect((await json(await me.GET(req("GET")))).body.error?.code).toBe(
      "no_profile",
    );
    expect(
      (
        await json(
          await start.POST(req("POST", { slug, difficulty: "standard" })),
        )
      ).status,
    ).toBe(403);
    const joined = await json<{ nickname: string }>(
      await me.POST(
        req("POST", {
          nickname: "Route tester",
          trainingLevel: "intern",
          consentResearch: false,
          agreed: true,
        }),
      ),
    );
    expect(joined.body.data?.nickname).toBe("Route tester");

    const started = await json<PlayerView>(
      await start.POST(req("POST", { slug, difficulty: "standard" })),
    );
    expect(started.status).toBe(200);
    const id = started.body.data?.encounterId ?? "";
    const responses: unknown[] = [list.body, started.body];

    for (const action of [
      { kind: "ask", item: "HX.MEDS.SUPPLEMENTS" },
      { kind: "order", item: "LAB.TOX.BLOOD_LEAD" },
      { kind: "wait" },
    ]) {
      const r = await json(await actions.POST(req("POST", action), params(id)));
      expect(r.status).toBe(200);
      responses.push(r.body);
    }
    const current = await json<PlayerView>(
      await view.GET(req("GET"), params(id)),
    );
    responses.push(current.body);
    expect(responses.flatMap((r) => scanForLeaks(prepared, r))).toEqual([]);

    expect((await json(await debrief.GET(req("GET"), params(id)))).status).toBe(
      409,
    );
    expect(
      (
        await json(
          await missing.POST(
            req("POST", {
              encounterId: id,
              kind: "test",
              query: "hair arsenic",
            }),
          ),
        )
      ).body.success,
    ).toBe(true);

    const chart = current.body.data?.chart ?? [];
    const evidence = [
      chart.find((e) => e.item === "HX.MEDS.SUPPLEMENTS")?.ref,
      chart.find((e) => e.component?.id === "CMP.PB_BLOOD")?.ref,
    ];
    const committed = await json<CommitResult>(
      await commit.POST(
        req("POST", {
          dx: "DX.LEAD_POISONING",
          evidence,
          plan: ["ACT.STOP_SUSPECTED_SOURCE"],
        }),
        params(id),
      ),
    );
    expect(committed.body.data).toMatchObject({ diagnosisAnchor: 5 });
    const opened = await json<DebriefView>(
      await debrief.GET(req("GET"), params(id)),
    );
    expect(opened.body.data?.finalDiagnosis.id).toBe("DX.LEAD_POISONING");
  });

  it("answers malformed and oversized bodies with a clear error", async () => {
    const start = await import("@/app/api/encounters/route");
    expect(
      (await json(await start.POST(req("POST", "{not json")))).body.error?.code,
    ).toBe("invalid_json");
    expect(
      (await json(await start.POST(req("POST", "x".repeat(20_001))))).status,
    ).toBe(413);
    expect(
      (await json(await start.POST(req("POST", { slug: "nope" })))).status,
    ).toBe(400);
  });
});

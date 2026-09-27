import { describe, expect, it } from "vitest";
import { ApiError, createApi } from "../src/lib/api";

function fakeFetch(
  status: number,
  body: unknown,
  seen: { url?: string; init?: RequestInit } = {},
) {
  return async (url: string, init: RequestInit) => {
    seen.url = url;
    seen.init = init;
    return new Response(
      typeof body === "string" ? body : JSON.stringify(body),
      { status },
    );
  };
}

describe("createApi", () => {
  it("sends the token and returns the envelope's data", async () => {
    const seen: { url?: string; init?: RequestInit } = {};
    const api = createApi(
      "http://api",
      async () => "tok",
      fakeFetch(
        200,
        { success: true, data: { encounterId: "e1" }, error: null },
        seen,
      ),
    );
    const view = await api.act("e/1", { kind: "wait" });
    expect(view.encounterId).toBe("e1");
    expect(seen.url).toBe("http://api/api/encounters/e%2F1/actions");
    expect((seen.init?.headers as Record<string, string>).authorization).toBe(
      "Bearer tok",
    );
    expect(seen.init?.body).toBe('{"kind":"wait"}');
  });

  it("turns an error envelope into an ApiError with its code", async () => {
    const api = createApi(
      "http://api",
      async () => "t",
      fakeFetch(422, {
        success: false,
        data: null,
        error: { code: "over_budget", message: "No budget" },
      }),
    );
    await expect(
      api.act("e", { kind: "order", item: "X" }),
    ).rejects.toMatchObject({
      status: 422,
      code: "over_budget",
      message: "No budget",
    });
  });

  it("explains an unreachable server and an unreadable reply", async () => {
    const offline = createApi(
      "http://api",
      async () => "t",
      async () => {
        throw new TypeError("fetch failed");
      },
    );
    await expect(offline.cases()).rejects.toMatchObject({ code: "offline" });
    const garbled = createApi(
      "http://api",
      async () => "t",
      fakeFetch(502, "<html>"),
    );
    await expect(garbled.cases()).rejects.toBeInstanceOf(ApiError);
    await expect(garbled.cases()).rejects.toMatchObject({
      code: "bad_response",
    });
  });

  it("reports a sign-in failure as such, not as a network problem", async () => {
    const api = createApi(
      "http://api",
      async () => {
        throw new Error("anonymous sign-ins are disabled");
      },
      fakeFetch(200, {}),
    );
    await expect(api.cases()).rejects.toMatchObject({
      code: "sign_in_failed",
      message: expect.stringContaining("anonymous sign-ins are disabled"),
    });
  });

  it("calls the global fetch bound to its owner by default", async () => {
    const original = globalThis.fetch;
    const calls: unknown[] = [];
    globalThis.fetch = function (
      this: unknown,
      ...args: Parameters<typeof fetch>
    ) {
      if (this !== undefined && this !== globalThis)
        throw new TypeError("Illegal invocation");
      calls.push(args[0]);
      return Promise.resolve(
        new Response(JSON.stringify({ success: true, data: [], error: null })),
      );
    } as typeof fetch;
    try {
      await createApi("http://api", async () => "t").cases();
      expect(calls).toEqual(["http://api/api/cases"]);
    } finally {
      globalThis.fetch = original;
    }
  });

  it("covers every endpoint", async () => {
    const urls: string[] = [];
    const ok = async (url: string) => {
      urls.push(url);
      return new Response(
        JSON.stringify({ success: true, data: {}, error: null }),
      );
    };
    const api = createApi("http://api", async () => "t", ok);
    await api.cases();
    await api.catalogue();
    await api.start({ slug: "c-abcde", difficulty: "standard" });
    await api.view("e");
    await api.commit("e", { dx: "DX.A", evidence: [], plan: [] });
    await api.debrief("e");
    await api.missing({ encounterId: "e", kind: "test", query: "x" });
    expect(urls.map((u) => u.replace("http://api", ""))).toEqual([
      "/api/cases",
      "/api/catalogue",
      "/api/encounters",
      "/api/encounters/e/view",
      "/api/encounters/e/commit",
      "/api/encounters/e/debrief",
      "/api/missing",
    ]);
  });
});

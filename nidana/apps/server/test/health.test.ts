import { describe, expect, it } from "vitest";
import { health } from "@/lib/health";

/** GET /api/health (N1.8): for the host's health check; no sign-in, and nothing about any case. */

describe("the health check", () => {
  it("says ok when the server's configuration and catalogue load", async () => {
    const response = await health(async () => ({}) as never);
    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({
      success: true,
      data: { status: "ok" },
      error: null,
    });
  });

  it("answers 503 without detail when the server cannot start", async () => {
    const response = await health(async () => {
      throw new Error("DATABASE_URL: required");
    });
    expect(response.status).toBe(503);
    const text = await response.text();
    expect(text).not.toContain("DATABASE_URL");
    expect(JSON.parse(text)).toMatchObject({
      success: false,
      error: { code: "unavailable" },
    });
  });
});

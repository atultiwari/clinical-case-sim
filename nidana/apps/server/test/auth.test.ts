import { describe, expect, it } from "vitest";
import { bearerToken, createVerifier } from "@/lib/auth";
import { createRateLimiter } from "@/lib/rate-limit";
import { ISSUER, SECRET, tokenFor } from "./helpers";

const PLAYER = "11111111-1111-4111-8111-111111111111";

describe("createVerifier", () => {
  const verifier = createVerifier({ jwtSecret: SECRET, issuer: ISSUER });

  it("accepts a signed-in player's token", async () => {
    expect(await verifier.verify(await tokenFor(PLAYER))).toEqual({
      playerId: PLAYER,
    });
  });

  it.each([
    ["a wrong signature", () => tokenFor(PLAYER, "y".repeat(40))],
    ["another audience", () => tokenFor(PLAYER, SECRET, "anon")],
    [
      "an expired token",
      () => tokenFor(PLAYER, SECRET, "authenticated", "-1m"),
    ],
    ["a subject that is not a user id", () => tokenFor("service_role")],
    ["garbage", async () => "not.a.token"],
    [
      "another issuer",
      () =>
        tokenFor(
          PLAYER,
          SECRET,
          "authenticated",
          "1h",
          "https://evil.example/auth/v1",
        ),
    ],
  ])("refuses %s", async (_label, make) => {
    expect(await verifier.verify(await make())).toBeNull();
  });

  it("needs a secret or a JWKS URL", () => {
    expect(() => createVerifier({ issuer: ISSUER })).toThrow(/SUPABASE/);
    expect(() =>
      createVerifier({ jwtSecret: "short", issuer: ISSUER }),
    ).toThrow(/SUPABASE/);
    expect(() =>
      createVerifier({
        jwksUrl: "https://example.supabase.co/auth/v1/.well-known/jwks.json",
        issuer: ISSUER,
      }),
    ).not.toThrow();
  });

  it("reads a bearer token", () => {
    expect(bearerToken("Bearer abc.def")).toBe("abc.def");
    expect(bearerToken("Basic abc")).toBeNull();
    expect(bearerToken(null)).toBeNull();
  });
});

describe("createRateLimiter", () => {
  it("allows the limit per window, per key", () => {
    let now = 0;
    const limiter = createRateLimiter(2, 1000, () => now);
    expect([
      limiter.take("a"),
      limiter.take("a"),
      limiter.take("a"),
      limiter.take("b"),
    ]).toEqual([true, true, false, true]);
    now = 1000;
    expect(limiter.take("a")).toBe(true);
  });
});

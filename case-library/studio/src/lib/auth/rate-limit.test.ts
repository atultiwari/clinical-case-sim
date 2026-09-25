import { describe, expect, it } from "vitest";

import { DEFAULT_RATE_LIMIT, LoginRateLimiter, loginKeys } from "@/lib/auth/rate-limit";

const MINUTE = 60_000;

function clock(start = 0) {
  let now = start;
  return { now: () => now, advance: (ms: number) => void (now += ms) };
}

describe("LoginRateLimiter", () => {
  it("locks a key after five failures for 15 minutes", () => {
    const time = clock();
    const limiter = new LoginRateLimiter(DEFAULT_RATE_LIMIT, time.now);
    const keys = loginKeys("203.0.113.9", "atul");
    for (let i = 0; i < 4; i += 1) limiter.recordFailure(keys);
    expect(limiter.isLocked(keys)).toBe(false);
    limiter.recordFailure(keys);
    expect(limiter.isLocked(keys)).toBe(true);
    time.advance(15 * MINUTE - 1);
    expect(limiter.isLocked(keys)).toBe(true);
    time.advance(1);
    expect(limiter.isLocked(keys)).toBe(false);
  });

  it("locks a username across addresses, and an address across usernames", () => {
    const limiter = new LoginRateLimiter(DEFAULT_RATE_LIMIT, clock().now);
    for (let i = 0; i < 5; i += 1) limiter.recordFailure(loginKeys(`198.51.100.${i}`, "atul"));
    expect(limiter.isLocked(loginKeys("192.0.2.1", "atul"))).toBe(true);
    expect(limiter.isLocked(loginKeys("192.0.2.1", "someone"))).toBe(false);

    for (let i = 0; i < 5; i += 1) limiter.recordFailure(loginKeys("192.0.2.50", `guess${i}`));
    expect(limiter.isLocked(loginKeys("192.0.2.50", "fresh"))).toBe(true);
  });

  it("forgets failures older than the window", () => {
    const time = clock();
    const limiter = new LoginRateLimiter(DEFAULT_RATE_LIMIT, time.now);
    const keys = loginKeys("192.0.2.7", "atul");
    for (let i = 0; i < 4; i += 1) limiter.recordFailure(keys);
    time.advance(15 * MINUTE);
    limiter.recordFailure(keys);
    expect(limiter.isLocked(keys)).toBe(false);
  });

  it("clears the count after a successful login", () => {
    const limiter = new LoginRateLimiter(DEFAULT_RATE_LIMIT, clock().now);
    const keys = loginKeys("192.0.2.7", "atul");
    for (let i = 0; i < 4; i += 1) limiter.recordFailure(keys);
    limiter.recordSuccess(keys);
    limiter.recordFailure(keys);
    expect(limiter.isLocked(keys)).toBe(false);
  });

  it("normalises usernames in its keys", () => {
    expect(loginKeys("a", "  ATUL ")).toEqual(["ip:a", "user:atul"]);
    expect(loginKeys("a", "x".repeat(500))[1]).toHaveLength(5 + 64);
  });

  it("keeps a bounded number of keys", () => {
    const limiter = new LoginRateLimiter({ ...DEFAULT_RATE_LIMIT, maxEntries: 10 }, clock().now);
    for (let i = 0; i < 50; i += 1) limiter.recordFailure([`ip:${i}`]);
    expect(limiter.size).toBeLessThanOrEqual(10);
  });
});

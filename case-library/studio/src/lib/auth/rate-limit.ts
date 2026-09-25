// Login rate limiting, in memory. After MAX_FAILURES failed attempts within the
// window, a key (a client address or a username) is locked for LOCKOUT_MS.
// Single instance only: the counts live in this process and reset on restart,
// which suits the Studio's one process on the VPS (README).

export type RateLimitPolicy = {
  maxFailures: number;
  windowMs: number;
  lockoutMs: number;
  /** Upper bound on remembered keys, so a flood of addresses cannot exhaust memory. */
  maxEntries: number;
};

export const DEFAULT_RATE_LIMIT: RateLimitPolicy = Object.freeze({
  maxFailures: 5,
  windowMs: 15 * 60 * 1000,
  lockoutMs: 15 * 60 * 1000,
  maxEntries: 10_000,
});

type Entry = Readonly<{ failures: number; windowStart: number; lockedUntil: number }>;

export function loginKeys(address: string, username: string): string[] {
  return [`ip:${address}`, `user:${username.trim().toLowerCase().slice(0, 64)}`];
}

export class LoginRateLimiter {
  private readonly entries = new Map<string, Entry>();
  private readonly policy: RateLimitPolicy;
  private readonly now: () => number;

  constructor(policy: RateLimitPolicy = DEFAULT_RATE_LIMIT, now: () => number = Date.now) {
    this.policy = policy;
    this.now = now;
  }

  /** True while any of the keys is locked. */
  isLocked(keys: readonly string[]): boolean {
    const now = this.now();
    return keys.some((key) => (this.entries.get(key)?.lockedUntil ?? 0) > now);
  }

  recordFailure(keys: readonly string[]): void {
    const now = this.now();
    for (const key of keys) {
      const current = this.entries.get(key);
      const fresh = !current || current.windowStart + this.policy.windowMs <= now;
      const failures = fresh ? 1 : current.failures + 1;
      const next: Entry = {
        failures,
        windowStart: fresh ? now : current.windowStart,
        lockedUntil: failures >= this.policy.maxFailures ? now + this.policy.lockoutMs : (current?.lockedUntil ?? 0),
      };
      this.entries.delete(key);
      this.entries.set(key, next);
    }
    this.prune(now);
  }

  recordSuccess(keys: readonly string[]): void {
    for (const key of keys) this.entries.delete(key);
  }

  get size(): number {
    return this.entries.size;
  }

  private prune(now: number): void {
    if (this.entries.size <= this.policy.maxEntries) return;
    for (const [key, entry] of this.entries) {
      if (entry.lockedUntil <= now && entry.windowStart + this.policy.windowMs <= now) this.entries.delete(key);
    }
    // Still too many: forget the oldest (Map keeps insertion order; updates re-insert).
    for (const key of this.entries.keys()) {
      if (this.entries.size <= this.policy.maxEntries) break;
      this.entries.delete(key);
    }
  }
}

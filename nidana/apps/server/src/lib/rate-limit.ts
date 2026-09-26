/**
 * Fixed-window rate limits per player (SPEC §6.5). In memory: the game server runs as one
 * process in development and on the VPS; a shared store is needed only if that changes.
 */

export interface RateLimiter {
  /** True if the key may make another request now. */
  take(key: string): boolean;
}

export function createRateLimiter(
  limit: number,
  windowMs: number,
  now: () => number = Date.now,
): RateLimiter {
  const windows = new Map<string, { start: number; count: number }>();
  return {
    take(key) {
      const time = now();
      if (windows.size > 10_000) {
        for (const [k, w] of windows)
          if (time - w.start >= windowMs) windows.delete(k);
      }
      const current = windows.get(key);
      if (current === undefined || time - current.start >= windowMs) {
        windows.set(key, { start: time, count: 1 });
        return true;
      }
      if (current.count >= limit) return false;
      windows.set(key, { start: current.start, count: current.count + 1 });
      return true;
    },
  };
}

import { useEffect, useState, type DependencyList } from "react";

/**
 * Loads data for a screen and ignores the answer if the screen has gone or its parameters
 * changed in the meantime, so a late reply never updates the wrong screen.
 */
export function useLoad<T>(
  load: () => Promise<T>,
  deps: DependencyList,
  fallbackError = "Could not load this page",
): { data: T | null; error: string | null } {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let live = true;
    setData(null);
    setError(null);
    load().then(
      (value) => {
        if (live) setData(value);
      },
      (e: unknown) => {
        if (live) setError(e instanceof Error ? e.message : fallbackError);
      },
    );
    return () => {
      live = false;
    };
    // The caller lists what the load depends on.
  }, deps);
  return { data, error };
}

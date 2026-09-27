import type { MissingRequest } from "@nidana/contracts/api";
import { normalise } from "./search";

/**
 * Missing requests (SPEC §6.2, N1.7): a search that finds nothing in the catalogue is reported
 * to the game server, which stores the bundle, kind and query and nothing about the player.
 * Reporting costs the player nothing and never shows an error; the no-match message is enough.
 */

/** The server's limit on a query (play.missing_request.query). */
export const MAX_MISSING_QUERY = 200;

/** How long the player must stop typing before an unmatched search is reported. */
export const MISSING_DELAY_MS = 1200;

/** The query to report, or null when the search is too short or found something. */
export function missingQuery(query: string, found: number): string | null {
  if (found > 0) return null;
  const tidy = query.trim().replace(/\s+/g, " ");
  if (normalise(tidy).length < 2) return null;
  return tidy.slice(0, MAX_MISSING_QUERY);
}

export type MissingReporter = (request: MissingRequest) => void;

/** Sends each unmatched query once per encounter and kind; a failed send may be retried later. */
export function createMissingReporter(
  send: (request: MissingRequest) => Promise<void>,
  onError: (error: unknown) => void = () => undefined,
): MissingReporter {
  const reported = new Set<string>();
  return (request) => {
    const key = `${request.encounterId}|${request.kind}|${normalise(request.query)}`;
    if (reported.has(key)) return;
    reported.add(key);
    send(request).catch((error: unknown) => {
      reported.delete(key);
      onError(error);
    });
  };
}

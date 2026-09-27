import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { MissingRequest, SearchItem } from "@nidana/contracts/api";
import { createApi, type Api } from "./api";
import { accessToken } from "./auth";
import { config } from "./config";
import {
  MISSING_DELAY_MS,
  createMissingReporter,
  missingQuery,
  type MissingReporter,
} from "./missing";

/** The API client and the catalogue, shared by every screen. */

interface Game {
  readonly api: Api;
  /** Shared by the workspace and the commit screen, so a query is reported once per encounter. */
  readonly reportMissing: MissingReporter;
}

const GameContext = createContext<Game | null>(null);

export function GameProvider({
  children,
  api,
}: {
  readonly children: ReactNode;
  readonly api?: Api;
}) {
  const value = useMemo<Game>(() => {
    const client = api ?? createApi(config.apiUrl, accessToken);
    return {
      api: client,
      reportMissing: createMissingReporter((r) => client.missing(r)),
    };
  }, [api]);
  return <GameContext.Provider value={value}>{children}</GameContext.Provider>;
}

function useGame(): Game {
  const game = useContext(GameContext);
  if (game === null) throw new Error("useApi must be used inside GameProvider");
  return game;
}

export function useApi(): Api {
  return useGame().api;
}

/**
 * Reports a search that found nothing once the player stops typing (N1.7). A search that is
 * changed, matched or left before the delay is not reported.
 */
export function useMissingReport(
  encounterId: string,
  kind: MissingRequest["kind"],
  query: string,
  found: number,
): void {
  const { reportMissing } = useGame();
  const unmatched = missingQuery(query, found);
  useEffect(() => {
    if (unmatched === null) return;
    const timer = setTimeout(
      () => reportMissing({ encounterId, kind, query: unmatched }),
      MISSING_DELAY_MS,
    );
    return () => clearTimeout(timer);
  }, [reportMissing, encounterId, kind, unmatched]);
}

let catalogueCache: Promise<SearchItem[]> | null = null;

/** The search catalogue, loaded once per app session. */
export function useCatalogue(): {
  items: SearchItem[] | null;
  error: string | null;
} {
  const api = useApi();
  const [items, setItems] = useState<SearchItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let live = true;
    catalogueCache ??= api.catalogue().catch((e: unknown) => {
      catalogueCache = null;
      throw e;
    });
    catalogueCache.then(
      (list) => live && setItems(list),
      (e: unknown) =>
        live &&
        setError(
          e instanceof Error ? e.message : "Could not load the catalogue",
        ),
    );
    return () => {
      live = false;
    };
  }, [api]);
  return { items, error };
}

/** A name for an item id, from the catalogue. */
export function nameOf(
  items: readonly SearchItem[] | null,
  id: string,
): string {
  return items?.find((i) => i.id === id)?.name ?? id;
}

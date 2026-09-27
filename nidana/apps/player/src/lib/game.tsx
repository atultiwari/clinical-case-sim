import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { SearchItem } from "@nidana/contracts/api";
import { createApi, type Api } from "./api";
import { accessToken } from "./auth";
import { config } from "./config";

/** The API client and the catalogue, shared by every screen. */

interface Game {
  readonly api: Api;
}

const GameContext = createContext<Game | null>(null);

export function GameProvider({
  children,
  api,
}: {
  readonly children: ReactNode;
  readonly api?: Api;
}) {
  const value = useMemo<Game>(
    () => ({ api: api ?? createApi(config.apiUrl, accessToken) }),
    [api],
  );
  return <GameContext.Provider value={value}>{children}</GameContext.Provider>;
}

export function useApi(): Api {
  const game = useContext(GameContext);
  if (game === null) throw new Error("useApi must be used inside GameProvider");
  return game.api;
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

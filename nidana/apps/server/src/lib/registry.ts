import type { CatalogueExport } from "@nidana/contracts";
import type { PreparedCase } from "@nidana/engine";
import { BundleRefusedError, verifyBundle, type BundleSource } from "./bundles";

/** The published cases, newest revision each, as players see them before play (SPEC §5.3, §5.14). */
export interface CaseCard {
  readonly slug: string;
  readonly title: string;
  readonly tags: readonly string[];
  readonly specialty: string | null;
  readonly difficulty: string | null;
  readonly estMinutes: number | null;
}

/**
 * Whether a role may see a case (S-006): cases whose licence forbids sharing adaptations (ND)
 * stay in the owner's own testing; testers see every other case.
 */
export function visibleTo(
  prepared: PreparedCase,
  role: "player" | "admin",
): boolean {
  if (role === "admin") return true;
  return !/(^|[^A-Z])ND([^A-Z]|$)/.test(prepared.bundle.source?.licence ?? "");
}

export interface Refused {
  readonly id: string;
  readonly code: BundleRefusedError["code"];
  readonly message: string;
}

export interface BundleRegistry {
  /** A published bundle by id, checked and prepared; cached. */
  load(id: string): Promise<PreparedCase>;
  /** The newest published revision for each case, by slug. */
  newestBySlug(): Promise<ReadonlyMap<string, PreparedCase>>;
  cases(role?: "player" | "admin"): Promise<readonly CaseCard[]>;
  /** Published bundles the server refused, with the reason. */
  refused(): Promise<readonly Refused[]>;
}

const REVISION = /^(?<case>.+)@v(?<version>\d+)\.r(?<revision>\d+)$/;

function rank(id: string): [number, number] {
  const groups = REVISION.exec(id)?.groups;
  return [Number(groups?.version ?? 0), Number(groups?.revision ?? 0)];
}

const newer = (a: string, b: string): boolean => {
  const [va, ra] = rank(a);
  const [vb, rb] = rank(b);
  return va > vb || (va === vb && ra > rb);
};

export function cardOf(prepared: PreparedCase): CaseCard {
  const card = prepared.bundle.case;
  return {
    slug: card.slug ?? "",
    title: card.display_title ?? "Untitled case",
    tags: card.display_tags ?? [],
    specialty: card.specialty ?? null,
    difficulty: card.difficulty ?? null,
    estMinutes: card.est_minutes ?? null,
  };
}

interface Index {
  readonly bySlug: ReadonlyMap<string, PreparedCase>;
  readonly refused: readonly Refused[];
}

export interface RegistryOptions {
  /** How long the list of published cases is kept before it is read again (default five minutes). */
  readonly refreshMs?: number;
  readonly now?: () => number;
}

export function createBundleRegistry(
  source: BundleSource,
  catalogue: CatalogueExport,
  options: RegistryOptions = {},
): BundleRegistry {
  const refreshMs = options.refreshMs ?? 5 * 60_000;
  const now = options.now ?? Date.now;
  // Published bundles never change, so prepared ones are kept; only the list of what is
  // published is read again, so a new revision reaches players without a restart.
  const cache = new Map<string, Promise<PreparedCase>>();
  let index: Promise<Index> | null = null;
  let builtAt = 0;

  const load = (id: string): Promise<PreparedCase> => {
    const cached = cache.get(id);
    if (cached !== undefined) return cached;
    const pending = source.read(id).then((stored) => {
      if (stored === null)
        throw new BundleRefusedError("not_found", `${id} is not published`);
      return verifyBundle(stored, catalogue);
    });
    // A refusal is not cached, so a corrected bundle can be picked up without a restart.
    pending.catch(() => cache.delete(id));
    cache.set(id, pending);
    return pending;
  };

  const buildIndex = async (): Promise<Index> => {
    const ids = await source.listPublished();
    const bySlug = new Map<string, PreparedCase>();
    const refused: Refused[] = [];
    for (const id of ids) {
      try {
        const prepared = await load(id);
        const slug = prepared.bundle.case.slug ?? "";
        const current = bySlug.get(slug);
        if (current === undefined || newer(id, current.bundle.bundle_id))
          bySlug.set(slug, prepared);
      } catch (error: unknown) {
        if (!(error instanceof BundleRefusedError)) throw error;
        refused.push({ id, code: error.code, message: error.message });
      }
    }
    return { bySlug, refused };
  };

  const getIndex = (): Promise<Index> => {
    if (index !== null && now() - builtAt >= refreshMs) index = null;
    if (index === null) builtAt = now();
    index ??= buildIndex().catch((error: unknown) => {
      index = null;
      throw error;
    });
    return index;
  };

  return {
    load,
    newestBySlug: async () => (await getIndex()).bySlug,
    cases: async (role = "player") =>
      [...(await getIndex()).bySlug.values()]
        .filter((p) => visibleTo(p, role))
        .map(cardOf)
        .sort((a, b) => a.title.localeCompare(b.title)),
    refused: async () => (await getIndex()).refused,
  };
}

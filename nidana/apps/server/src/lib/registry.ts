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
  cases(): Promise<readonly CaseCard[]>;
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

function cardOf(prepared: PreparedCase): CaseCard {
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

export function createBundleRegistry(
  source: BundleSource,
  catalogue: CatalogueExport,
): BundleRegistry {
  const cache = new Map<string, Promise<PreparedCase>>();
  let index: Promise<Index> | null = null;

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
    index ??= buildIndex().catch((error: unknown) => {
      index = null;
      throw error;
    });
    return index;
  };

  return {
    load,
    newestBySlug: async () => (await getIndex()).bySlug,
    cases: async () =>
      [...(await getIndex()).bySlug.values()]
        .map(cardOf)
        .sort((a, b) => a.title.localeCompare(b.title)),
    refused: async () => (await getIndex()).refused,
  };
}

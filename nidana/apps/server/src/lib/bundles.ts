import { readFile, readdir } from "node:fs/promises";
import { join } from "node:path";
import {
  PINNED_BUNDLE_SCHEMA_VERSION,
  PINNED_CATALOGUE_VERSION,
  parseBundleJson,
  type CatalogueExport,
} from "@nidana/contracts";
import { prepareCase, type PreparedCase } from "@nidana/engine";
import { canonicalJson, sha256Hex } from "./canonical-json";

/**
 * Where published bundles come from, and the checks every bundle passes before play
 * (SPEC §4): its SHA-256, its schema version and its catalogue version (nidana/CLAUDE.md pins).
 */

export interface StoredBundle {
  readonly id: string;
  /** The bundle as the exported file's bytes (RFC 8785). */
  readonly text: string;
  /** The SHA-256 recorded when it was exported. */
  readonly sha256: string;
}

export interface BundleSource {
  /** Ids of every published bundle. */
  listPublished(): Promise<readonly string[]>;
  read(id: string): Promise<StoredBundle | null>;
}

export type BundleRefusal =
  | "not_found"
  | "hash_mismatch"
  | "invalid_bundle"
  | "unsupported_schema"
  | "unsupported_catalogue";

export class BundleRefusedError extends Error {
  readonly code: BundleRefusal;

  constructor(code: BundleRefusal, message: string) {
    super(message);
    this.name = "BundleRefusedError";
    this.code = code;
  }
}

const BUNDLE_FILE = /^(.+@v\d+\.r\d+)\.json$/;

/** The Case Library's exported files (development and tests): every export counts as published. */
export function fileBundleSource(directory: string): BundleSource {
  return {
    async listPublished() {
      const names = await readdir(directory);
      return names.flatMap((name) => BUNDLE_FILE.exec(name)?.[1] ?? []).sort();
    },
    async read(id) {
      try {
        const [text, hash] = await Promise.all([
          readFile(join(directory, `${id}.json`), "utf8"),
          readFile(join(directory, `${id}.json.sha256`), "utf8"),
        ]);
        return { id, text, sha256: hash.trim().split(/\s+/)[0] ?? "" };
      } catch (error: unknown) {
        if ((error as NodeJS.ErrnoException).code === "ENOENT") return null;
        throw error;
      }
    },
  };
}

/** Checks a stored bundle and prepares it for play, or refuses it with a reason. */
export function verifyBundle(
  stored: StoredBundle,
  catalogue: CatalogueExport,
): PreparedCase {
  if (sha256Hex(stored.text) !== stored.sha256) {
    throw new BundleRefusedError(
      "hash_mismatch",
      `${stored.id}: the SHA-256 does not match the recorded hash`,
    );
  }
  const parsed = parseBundleJson(stored.text);
  if (!parsed.success) {
    const version = (() => {
      try {
        return (JSON.parse(stored.text) as { schema_version?: unknown })
          .schema_version;
      } catch {
        return undefined;
      }
    })();
    if (version !== undefined && version !== PINNED_BUNDLE_SCHEMA_VERSION) {
      throw new BundleRefusedError(
        "unsupported_schema",
        `${stored.id}: schema ${String(version)} is not supported (pinned ${PINNED_BUNDLE_SCHEMA_VERSION})`,
      );
    }
    throw new BundleRefusedError(
      "invalid_bundle",
      `${stored.id}: ${parsed.error.message}`,
    );
  }
  const bundle = parsed.data;
  if (bundle.bundle_id !== stored.id) {
    throw new BundleRefusedError(
      "invalid_bundle",
      `${stored.id}: the file holds ${bundle.bundle_id}`,
    );
  }
  if (
    bundle.catalogue_version !== catalogue.version ||
    catalogue.version !== PINNED_CATALOGUE_VERSION
  ) {
    throw new BundleRefusedError(
      "unsupported_catalogue",
      `${stored.id}: catalogue v${bundle.catalogue_version} is not supported (pinned v${PINNED_CATALOGUE_VERSION})`,
    );
  }
  return prepareCase(bundle, catalogue);
}

/** Re-serializes a stored body (jsonb) so its hash can be checked against the exported file's. */
export function storedFromBody(
  id: string,
  body: unknown,
  sha256: string,
): StoredBundle {
  return { id, text: canonicalJson(body), sha256 };
}

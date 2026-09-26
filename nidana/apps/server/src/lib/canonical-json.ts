import { createHash } from "node:crypto";

/**
 * RFC 8785 (JSON Canonicalization Scheme): the serializer the Case Library writes bundles with
 * (case-library/scripts/jcs.py). Re-serializing a stored bundle body this way reproduces the
 * exported file's bytes, so its SHA-256 can be checked (Case Library SPEC §10.5).
 */
export function canonicalJson(value: unknown): string {
  if (value === null || typeof value === "boolean")
    return JSON.stringify(value);
  if (typeof value === "number") {
    if (!Number.isFinite(value))
      throw new Error(`JSON cannot hold ${value}: numbers must be finite`);
    return JSON.stringify(value);
  }
  if (typeof value === "string") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  if (typeof value === "object") {
    const entries = Object.entries(value as Record<string, unknown>);
    const undefinedKey = entries.find(([, v]) => v === undefined);
    if (undefinedKey !== undefined)
      throw new Error(`JSON cannot hold undefined (key "${undefinedKey[0]}")`);
    // Default string comparison orders by UTF-16 code units, as RFC 8785 §3.2.3 requires.
    const sorted = entries.sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0));
    return `{${sorted.map(([k, v]) => `${JSON.stringify(k)}:${canonicalJson(v)}`).join(",")}}`;
  }
  throw new Error(`JSON cannot hold a ${typeof value}`);
}

export function sha256Hex(text: string): string {
  return createHash("sha256").update(text, "utf8").digest("hex");
}

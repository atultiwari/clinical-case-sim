import type { PreparedCase } from "@nidana/engine";

/**
 * The leak scan of SPEC §6.4, run on every encounter response before the debrief. Returns a
 * description of each leak found; an empty list means the response is clean.
 */

const FORBIDDEN_KEYS = new Set([
  "origin",
  "origins",
  "tier",
  "rationale",
  "judgement_call",
  "confidence",
  "ground_truth",
  "rubric",
  "must_do",
  "must_not_do",
  "test_utility",
  "path_analysis",
  "key_discriminators",
  "bundle_id",
  "bundleId",
  "pmcid",
  "doi",
  "citation",
  "attribution",
  "findings",
  "based_on",
  "released_by",
  "catalogue_ref",
  "reveals_dx",
  "pivotal",
  "formula",
  "gap_id",
  "raw_material",
  "file_path",
  "source_locator",
  "source",
  "table",
]);

/** Keys holding the player's own entries, left out of the word scan (SPEC §6.4). */
const PLAYER_OWN = new Set(["differential"]);

function walk(
  value: unknown,
  path: string,
  visit: (path: string, key: string | null, value: unknown) => void,
): void {
  visit(path, path.split(".").at(-1) ?? null, value);
  if (Array.isArray(value))
    value.forEach((v, i) => walk(v, `${path}[${i}]`, visit));
  else if (value !== null && typeof value === "object") {
    for (const [k, v] of Object.entries(value)) walk(v, `${path}.${k}`, visit);
  }
}

const escape = (text: string): string =>
  text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

export function diagnosisWords(prepared: PreparedCase): string[] {
  const finalDx = prepared.bundle.ground_truth.final_dx as {
    id?: string;
    accepted_synonyms?: string[];
  };
  const item = prepared.items.get(finalDx.id ?? "");
  return [
    ...(finalDx.accepted_synonyms ?? []),
    item?.name ?? "",
    ...(item?.synonyms ?? []),
  ].filter((w) => w.length >= 4);
}

export function scanForLeaks(
  prepared: PreparedCase,
  response: unknown,
): string[] {
  const leaks: string[] = [];
  const { bundle } = prepared;
  const rowIds = new Set([
    ...bundle.facts.map((f) => f.id),
    ...bundle.ledger.map((l) => l.id),
    ...bundle.reports.map((r) => r.id),
    ...bundle.consult_notes.map((c) => c.id),
    ...bundle.raw_material.map((r) => r.id),
    ...bundle.media.map((m) => m.id),
    ...bundle.gaps.map((g) => g.id),
  ]);
  const words = diagnosisWords(prepared).map(
    (w) => new RegExp(`\\b${escape(w)}\\b`, "i"),
  );
  walk(response, "$", (path, key, value) => {
    const own = path.split(/[.[]/).some((part) => PLAYER_OWN.has(part));
    if (key !== null && FORBIDDEN_KEYS.has(key.replace(/\[\d+\]$/, "")))
      leaks.push(`${path}: forbidden key`);
    if (typeof value !== "string") return;
    if (/PMC\d{4,}/.test(value) || /\b10\.\d{4,}\//.test(value))
      leaks.push(`${path}: source identifier`);
    if (rowIds.has(value)) leaks.push(`${path}: bundle row id ${value}`);
    if (!own) {
      const word = words.find((re) => re.test(value));
      if (word !== undefined)
        leaks.push(`${path}: diagnosis word ${word.source}`);
    }
  });
  return leaks;
}

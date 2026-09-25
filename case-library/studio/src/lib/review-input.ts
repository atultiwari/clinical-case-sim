// Strict validation of what the Studio's write forms send (SPEC §7.2, §9).
// Every field is checked against an allow-list or a narrow pattern before it
// reaches the database; the database then checks that the ids exist in the case.

import type { Json } from "@/lib/ground-truth";

export const REVIEW_TARGET_TABLES = ["synthetic_ledger", "report", "consult_note", "fact"] as const;
export type ReviewTargetTable = (typeof REVIEW_TARGET_TABLES)[number];

/** SPEC §7.2: Approve, Edit (with the new value) or Reject. */
export const REVIEW_DECISIONS = ["approve", "edit", "reject"] as const;
export type ReviewDecisionValue = (typeof REVIEW_DECISIONS)[number];

/** SPEC §9: use, mask or exclude ('pending' is only the starting state). */
export const FIGURE_DECISIONS = ["use", "mask", "exclude"] as const;
export type FigureDecisionValue = (typeof FIGURE_DECISIONS)[number];

export const MAX_EDITED_LENGTH = 4000;
export const MAX_NOTE_LENGTH = 1000;

const CASE_VERSION_ID = /^(PMC[0-9]+|NID-[0-9]{4,})@v[0-9]+$/;
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;
const ROW_ID = /^[A-Za-z0-9][A-Za-z0-9._:-]{0,99}$/;
const MEDIA_ID = /^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$/;
const MASKED_FILE = /^[A-Za-z0-9][A-Za-z0-9_-]*(\.[A-Za-z0-9_-]+)*\.(png|jpe?g|webp|gif|tiff?)$/i;
const MAX_MASKED_FILE_LENGTH = 128;

export type ReviewDecisionInput = {
  caseVersionId: string;
  targetTable: ReviewTargetTable;
  rowId: string;
  decision: ReviewDecisionValue;
  edited: Json | null;
  note: string | null;
};

export type FigureDecisionInput = {
  caseVersionId: string;
  mediaId: string;
  decision: FigureDecisionValue;
  maskedPath: string | null;
};

export type Validation<T> = { ok: true; value: T } | { ok: false; error: string };

type FieldSource = { get(name: string): unknown };

function text(source: FieldSource, name: string): string | null {
  const value = source.get(name);
  return typeof value === "string" ? value : null;
}

function oneOf<T extends string>(values: readonly T[], value: string | null): T | null {
  return value !== null && (values as readonly string[]).includes(value) ? (value as T) : null;
}

export function isCaseVersionId(value: string | null): value is string {
  return value !== null && CASE_VERSION_ID.test(value);
}

/** The case id of a case version id: 'PMC12949993@v1' → 'PMC12949993'. */
export function caseIdOf(caseVersionId: string): string {
  return caseVersionId.slice(0, caseVersionId.indexOf("@"));
}

export function isRowId(targetTable: ReviewTargetTable, value: string | null): value is string {
  if (value === null) return false;
  return targetTable === "synthetic_ledger" ? UUID.test(value) : ROW_ID.test(value);
}

/**
 * review_decision.target_id: the ledger's uuid, or '<case version>/<row id>' for
 * tables keyed by case version and id (the form the Studio's review history reads).
 */
export function reviewTargetId(targetTable: ReviewTargetTable, caseVersionId: string, rowId: string): string {
  return targetTable === "synthetic_ledger" ? rowId : `${caseVersionId}/${rowId}`;
}

/** The new value: JSON if it parses (e.g. {"value": 80} or 80), otherwise the text itself. */
export function parseEditedValue(raw: string): Json {
  try {
    return JSON.parse(raw) as Json;
  } catch {
    return raw;
  }
}

export function parseReviewDecision(source: FieldSource): Validation<ReviewDecisionInput> {
  const caseVersionId = text(source, "caseVersionId");
  if (!isCaseVersionId(caseVersionId)) return { ok: false, error: "Unknown case version." };
  const targetTable = oneOf(REVIEW_TARGET_TABLES, text(source, "targetTable"));
  if (!targetTable) return { ok: false, error: "Unknown kind of row." };
  const rowId = text(source, "rowId");
  if (!isRowId(targetTable, rowId)) return { ok: false, error: "Unknown row." };
  const decision = oneOf(REVIEW_DECISIONS, text(source, "decision"));
  if (!decision) return { ok: false, error: "Choose approve, edit or reject." };

  const editedRaw = (text(source, "edited") ?? "").trim();
  if (editedRaw.length > MAX_EDITED_LENGTH) {
    return { ok: false, error: `The new value is longer than ${MAX_EDITED_LENGTH} characters.` };
  }
  if (decision === "edit" && editedRaw === "") return { ok: false, error: "An edit needs the new value." };

  const note = (text(source, "note") ?? "").trim();
  if (note.length > MAX_NOTE_LENGTH) {
    return { ok: false, error: `The note is longer than ${MAX_NOTE_LENGTH} characters.` };
  }

  return {
    ok: true,
    value: {
      caseVersionId,
      targetTable,
      rowId,
      decision,
      // Only an edit carries a new value; any text sent with approve or reject is dropped.
      edited: decision === "edit" ? parseEditedValue(editedRaw) : null,
      note: note || null,
    },
  };
}

/** A masked copy lives beside the figure in case-media: '<case id>/<file>'. */
export function isMaskedPath(caseVersionId: string, value: string): boolean {
  const prefix = `${caseIdOf(caseVersionId)}/`;
  if (!value.startsWith(prefix)) return false;
  const file = value.slice(prefix.length);
  return file.length <= MAX_MASKED_FILE_LENGTH && !file.includes("..") && MASKED_FILE.test(file);
}

export function parseFigureDecision(source: FieldSource): Validation<FigureDecisionInput> {
  const caseVersionId = text(source, "caseVersionId");
  if (!isCaseVersionId(caseVersionId)) return { ok: false, error: "Unknown case version." };
  const mediaId = text(source, "mediaId");
  if (mediaId === null || !MEDIA_ID.test(mediaId)) return { ok: false, error: "Unknown figure." };
  const decision = oneOf(FIGURE_DECISIONS, text(source, "decision"));
  if (!decision) return { ok: false, error: "Choose use, mask or exclude." };

  const maskedPath = (text(source, "maskedPath") ?? "").trim();
  if (decision !== "mask") return { ok: true, value: { caseVersionId, mediaId, decision, maskedPath: null } };
  if (!isMaskedPath(caseVersionId, maskedPath)) {
    return {
      ok: false,
      error: `Mask needs the masked copy's path in case-media, such as ${caseIdOf(caseVersionId)}/${mediaId}-masked.png.`,
    };
  }
  return { ok: true, value: { caseVersionId, mediaId, decision, maskedPath } };
}

/** 'studio-<YYYY-MM-DD>-<username>', with '-<n>' once that batch has been applied. */
export function studioBatchId(date: Date, username: string, sequence = 1): string {
  const day = date.toISOString().slice(0, 10);
  const base = `studio-${day}-${username}`;
  return sequence <= 1 ? base : `${base}-${sequence}`;
}

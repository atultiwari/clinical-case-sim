/**
 * Ground-truth JSON as stored (SPEC §10.4). The shapes are checked here rather
 * than trusted: anything unexpected is still shown, as raw JSON.
 */
export type Json = null | boolean | number | string | Json[] | { [key: string]: Json };

export type ConditionItem = { text: string; condition: Json | null };
export type RubricAnchor = { score: number | null; text: string; condition: Json | null };
export type Rubric = { anchors: RubricAnchor[]; defaultScore: number | null; unparsed: Json | null };

function isRecord(value: unknown): value is Record<string, Json> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function textOf(value: Record<string, Json>): string {
  const text = value.text ?? value.label ?? value.name ?? value.id;
  return typeof text === "string" ? text : JSON.stringify(value);
}

function conditionOf(value: Record<string, Json>): Json | null {
  return value.if ?? value.condition ?? null;
}

/** must_do and must_not_do: a list of { text, if } (or plain strings). */
export function conditionItems(value: Json | null | undefined): ConditionItem[] {
  if (!Array.isArray(value)) return [];
  return value.map((entry) =>
    isRecord(entry)
      ? { text: textOf(entry), condition: conditionOf(entry) }
      : { text: typeof entry === "string" ? entry : JSON.stringify(entry), condition: null },
  );
}

function anchorOf(entry: Json): RubricAnchor {
  if (!isRecord(entry)) {
    return { score: null, text: typeof entry === "string" ? entry : JSON.stringify(entry), condition: null };
  }
  const score = typeof entry.score === "number" ? entry.score : null;
  return { score, text: textOf(entry), condition: conditionOf(entry) };
}

/** The rubric: { rubric: [anchors], default_score } or a bare list of anchors. */
export function parseRubric(value: Json | null | undefined): Rubric {
  if (value === null || value === undefined) return { anchors: [], defaultScore: null, unparsed: null };
  if (Array.isArray(value)) return { anchors: value.map(anchorOf), defaultScore: null, unparsed: null };
  if (isRecord(value)) {
    const list = value.rubric ?? value.anchors;
    if (Array.isArray(list)) {
      const defaultScore = typeof value.default_score === "number" ? value.default_score : null;
      return { anchors: list.map(anchorOf), defaultScore, unparsed: null };
    }
  }
  return { anchors: [], defaultScore: null, unparsed: value };
}

/** The final diagnosis: { id, text } or a string. */
export function diagnosisLabel(value: Json | null | undefined): { id: string | null; text: string } {
  if (typeof value === "string") return { id: null, text: value };
  if (isRecord(value)) {
    const id = typeof value.id === "string" ? value.id : null;
    const text = typeof value.text === "string" ? value.text : (id ?? JSON.stringify(value));
    return { id, text };
  }
  return { id: null, text: value === null || value === undefined ? "—" : JSON.stringify(value) };
}

/** Pretty-printed JSON for display. */
export function prettyJson(value: unknown): string {
  return value === undefined ? "" : JSON.stringify(value, null, 2);
}

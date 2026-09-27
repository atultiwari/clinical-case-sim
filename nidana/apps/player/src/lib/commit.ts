/** The commit form's rules (SPEC §5.12), checked in the app before the server checks them again. */

export const MAX_EVIDENCE = 5;

export interface CommitDraft {
  readonly dx: string | null;
  readonly evidence: readonly string[];
  readonly plan: readonly string[];
}

export function commitProblems(draft: CommitDraft): string[] {
  const problems: string[] = [];
  if (draft.dx === null) problems.push("Choose a final diagnosis.");
  if (draft.evidence.length > MAX_EVIDENCE)
    problems.push(`Cite at most ${MAX_EVIDENCE} items as key evidence.`);
  if (new Set(draft.plan).size !== draft.plan.length)
    problems.push("Each plan item may appear only once.");
  return problems;
}

/** Adds or removes a Chart reference from the evidence, keeping the limit. */
export function toggleEvidence(
  evidence: readonly string[],
  ref: string,
): string[] {
  if (evidence.includes(ref)) return evidence.filter((r) => r !== ref);
  return evidence.length >= MAX_EVIDENCE ? [...evidence] : [...evidence, ref];
}

/** Moves a plan item up (-1) or down (+1); order matters where the rules say so. */
export function movePlanItem(
  plan: readonly string[],
  index: number,
  step: -1 | 1,
): string[] {
  const target = index + step;
  if (index < 0 || index >= plan.length || target < 0 || target >= plan.length)
    return [...plan];
  const next = [...plan];
  [next[index], next[target]] = [next[target] as string, next[index] as string];
  return next;
}

import { Condition } from "@nidana/contracts";
import { z } from "zod";
import { EngineError } from "./errors.ts";
import type { PreparedCase } from "./prepare.ts";

/**
 * The parts of a bundle's ground truth that scoring reads. Schema 0.3 leaves the rubric and
 * the final diagnosis loosely typed, so they are checked here before use.
 */

const Anchor = z.number().int().min(1).max(5);

const Rubric = z.looseObject({
  default_score: Anchor,
  rubric: z.array(
    z.looseObject({ score: Anchor, text: z.string(), if: Condition }),
  ),
});

const FinalDx = z.looseObject({ id: z.string().regex(/^DX\./) });

export interface ScoredRule {
  readonly text: string;
  /** Null for a plain-text item from schema 0.2, which the engine cannot evaluate. */
  readonly condition: Condition | null;
}

export interface GroundTruth {
  readonly finalDx: string;
  readonly defaultAnchor: number;
  /** Highest score first. */
  readonly anchors: readonly {
    readonly score: number;
    readonly text: string;
    readonly condition: Condition;
  }[];
  readonly mustDo: readonly ScoredRule[];
  readonly mustNotDo: readonly ScoredRule[];
}

function rules(
  items:
    readonly (string | { text: string; if?: Condition })[] | null | undefined,
): ScoredRule[] {
  return (items ?? []).map((item) =>
    typeof item === "string"
      ? { text: item, condition: null }
      : { text: item.text, condition: item.if ?? null },
  );
}

export function groundTruthOf(prepared: PreparedCase): GroundTruth {
  const truth = prepared.bundle.ground_truth;
  const rubric = Rubric.safeParse(truth.rubric);
  const finalDx = FinalDx.safeParse(truth.final_dx);
  if (!rubric.success || !finalDx.success) {
    const error = rubric.error ?? finalDx.error;
    throw new EngineError(
      "invalid_ground_truth",
      `${prepared.bundle.bundle_id}: the rubric or final diagnosis cannot be scored: ${error ? z.prettifyError(error) : ""}`,
    );
  }
  return {
    finalDx: finalDx.data.id,
    defaultAnchor: rubric.data.default_score,
    anchors: [...rubric.data.rubric]
      // Array.prototype.sort is stable, so anchors with the same score keep the bundle's order.
      .sort((a, b) => b.score - a.score)
      .map((a) => ({ score: a.score, text: a.text, condition: a.if })),
    mustDo: rules(truth.must_do),
    mustNotDo: rules(truth.must_not_do),
  };
}

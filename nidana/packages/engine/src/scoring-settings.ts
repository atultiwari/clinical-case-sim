import { z } from "zod";
import { EngineError } from "./errors.ts";

/** Scoring weights (nidana/configs/scoring.json; SPEC §7.1). Every score records `version`. */

const Points = z.number().min(0);

export const ScoringSettings = z.strictObject({
  version: z.string().min(1),
  diagnosis: z.strictObject({
    points_by_anchor: z.strictObject({
      "5": Points,
      "4": Points,
      "3": Points,
      "2": Points,
      "1": Points,
    }),
  }),
  management: z.strictObject({ points: Points }),
  efficiency: z.strictObject({
    cost_points: Points,
    test_points: Points,
    unnecessary_test_penalty: Points,
    risky_test_penalty: Points,
    /** Tests with no utility in the bundle count as supportive if listed here, otherwise unnecessary (Case Library SPEC §6.8). */
    routine_tests: z.array(z.string()),
    time_points: Points,
  }),
  reasoning: z.strictObject({
    differential_points: Points,
    discriminator_points: Points,
    referral_points: Points,
    referral_penalty: Points,
  }),
  safety: z.strictObject({ penalty_per_violation: Points, cap_total: Points }),
});
export type ScoringSettings = z.infer<typeof ScoringSettings>;

export function parseScoringSettings(input: unknown): ScoringSettings {
  const result = ScoringSettings.safeParse(input);
  if (result.success) return result.data;
  throw new EngineError(
    "invalid_settings",
    `Invalid scoring settings: ${z.prettifyError(result.error)}`,
  );
}

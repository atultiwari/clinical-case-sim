import { z } from "zod";
import { EngineError } from "./errors.ts";

/** Difficulty settings (nidana/configs/difficulty.json; SPEC §5.4 and §5.9). */

export const Difficulty = z.enum(["guided", "standard", "expert"]);
export type Difficulty = z.infer<typeof Difficulty>;

const Minutes = z.number().int().positive();

const Level = z.strictObject({
  /** The first report an interpretive test with two versions returns (N-014). */
  first_report: z.enum(["provisional", "final"]),
  /** Budget in INR as a multiple of the efficient path's test prices. */
  budget_factor: z.number().positive(),
  referrals_allowed: z.number().int().min(0),
});
export type Level = z.infer<typeof Level>;

export const DifficultySettings = z.strictObject({
  clock: z.strictObject({
    ask_minutes: Minutes,
    examine_minutes: Minutes,
    referral_minutes: Minutes,
    max_stay_minutes: Minutes,
  }),
  difficulties: z.strictObject({
    guided: Level,
    standard: Level,
    expert: Level,
  }),
});
export type DifficultySettings = z.infer<typeof DifficultySettings>;

export function parseDifficultySettings(input: unknown): DifficultySettings {
  const result = DifficultySettings.safeParse(input);
  if (result.success) return result.data;
  throw new EngineError(
    "invalid_settings",
    `Invalid difficulty settings: ${z.prettifyError(result.error)}`,
  );
}

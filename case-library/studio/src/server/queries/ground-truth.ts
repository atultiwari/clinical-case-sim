import "server-only";

import type { Json } from "@/lib/ground-truth";
import { withReader } from "@/server/db";

export type GroundTruthRow = {
  final_dx: Json;
  accepted_differential: Json | null;
  red_herrings: Json | null;
  key_discriminators: Json | null;
  rubric: Json | null;
  must_do: Json | null;
  must_not_do: Json | null;
  efficient_path: Json | null;
  teaching_points: Json | null;
  treatment_given: string | null;
  outcome: string | null;
};

export type TestUtilityRow = { test_item_id: string; test_name: string | null; utility: string; rationale: string | null };

export async function getGroundTruth(caseVersionId: string): Promise<GroundTruthRow | null> {
  const rows = await withReader((sql) => sql<GroundTruthRow[]>`
    select final_dx, accepted_differential, red_herrings, key_discriminators, rubric, must_do,
           must_not_do, efficient_path, teaching_points, treatment_given, outcome
    from casevault.ground_truth
    where case_version_id = ${caseVersionId}
  `);
  return rows[0] ?? null;
}

export async function listTestUtility(caseVersionId: string): Promise<TestUtilityRow[]> {
  return withReader((sql) => sql<TestUtilityRow[]>`
    select u.test_item_id, ci.name as test_name, u.utility, u.rationale
    from casevault.test_utility u
    left join casevault.catalogue_item ci on ci.id = u.test_item_id
    where u.case_version_id = ${caseVersionId}
    order by array_position(array['essential','supportive','low_yield','unnecessary','risky'], u.utility),
             u.test_item_id
  `);
}

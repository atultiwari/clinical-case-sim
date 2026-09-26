// Generated from case-library/schemas/case-bundle.v0.3.schema.json by
// `pnpm --filter @nidana/contracts generate`. Do not edit by hand; a test checks it is current.
import { z } from "zod";

/** Days from day 0; null means valid throughout the admission. */
export const Day = z.number().int().nullable();
export type Day = z.infer<typeof Day>;

export const Release = z
  .string()
  .regex(new RegExp("^(vignette|chart|never|service\\.[a-z_]+)$"));
export type Release = z.infer<typeof Release>;

export const Fact = z.looseObject({
  id: z.string(),
  category: z.string(),
  item: z.string(),
  catalogue_ref: z.string().nullable().optional(),
  released_by: z.array(z.string()).optional(),
  code_system: z.string().nullable().optional(),
  code: z.string().nullable().optional(),
  value: z.string().nullable().optional(),
  value_num: z.number().nullable().optional(),
  unit: z.string().nullable().optional(),
  ref_range: z.string().nullable().optional(),
  flag: z.string().nullable().optional(),
  get day() {
    return Day;
  },
  kind: z.enum(["raw", "interpretation"]).optional(),
  origin: z.enum(["article", "derived"]),
  formula: z.string().nullable().optional(),
  reveals_dx: z.boolean().optional(),
  pivotal: z.boolean().optional(),
  get release() {
    return Release;
  },
  release_condition: z.record(z.string(), z.unknown()).nullable().optional(),
  release_text: z.string().nullable().optional(),
  lay_text: z.string().nullable().optional(),
  source_locator: z.string().nullable().optional(),
});
export type Fact = z.infer<typeof Fact>;

export const LedgerRow = z.looseObject({
  id: z.string(),
  target: z.string(),
  get day_bucket() {
    return Day;
  },
  tier: z.enum(["affected", "normal", "rule", "reviewer"]),
  gap_id: z.string().nullable().optional(),
  value: z.record(z.string(), z.unknown()),
  release_text: z.string().nullable().optional(),
  lay_text: z.string().nullable().optional(),
});
export type LedgerRow = z.infer<typeof LedgerRow>;

const ReportIf1 = z.looseObject({ variant: z.literal("original").optional() });
const ReportThen2 = z.looseObject({
  status: z.literal("provisional").optional(),
  status_line: z.string(),
});
export const Report = z
  .looseObject({
    id: z.string(),
    test_item_id: z.string().nullable().optional(),
    variant: z.enum(["original", "expert", "only"]),
    status: z.enum(["provisional", "final"]),
    status_line: z.string().nullable().optional(),
    findings: z.array(z.string().regex(new RegExp("^FND\\."))),
    report_text: z.string().nullable().optional(),
    impression: z.string().nullable().optional(),
    suggested_reflex: z.array(z.string()).optional(),
    based_on: z.array(z.string()).optional(),
    origins: z
      .array(z.enum(["article", "affected", "normal", "rule", "reviewer"]))
      .optional(),
  })
  .superRefine(
    (value, ctx) => {
      if (ReportIf1.safeParse(value).success) {
        const result = ReportThen2.safeParse(value);
        for (const issue of result.error?.issues ?? []) {
          ctx.addIssue({
            code: "custom",
            path: issue.path,
            message: `${issue.message} (when variant is "original")`,
          });
        }
      }
    },
    {
      when: ({ value }) =>
        typeof value === "object" && value !== null && !Array.isArray(value),
    },
  );
export type Report = z.infer<typeof Report>;

export const ConsultNote = z.looseObject({
  id: z.string(),
  specialty: z.string(),
  variant: z.number().int().min(1),
  get condition() {
    return ConditionOrNull.optional();
  },
  note_text: z.string(),
  recommendations: z.array(z.string()).optional(),
  origin: z.enum(["affected", "rule"]),
});
export type ConsultNote = z.infer<typeof ConsultNote>;

export const RawMaterial = z.looseObject({
  id: z.string(),
  test: z.string(),
  test_item_id: z.string().nullable().optional(),
  get release() {
    return Release;
  },
  get day() {
    return Day.optional();
  },
  findings: z.string(),
  media: z.array(z.string()).optional(),
  note: z.string().nullable().optional(),
  source_locator: z.string().nullable().optional(),
});
export type RawMaterial = z.infer<typeof RawMaterial>;

export const Media = z.looseObject({
  id: z.string(),
  figure: z.string().nullable().optional(),
  specimen: z.string().nullable().optional(),
  stain: z.string().nullable().optional(),
  file_path: z.string().nullable().optional(),
  redacted_caption: z.string().nullable().optional(),
  licence: z.string(),
  production_ok: z.boolean(),
  public_release_ok: z.boolean(),
  has_annotations: z.boolean(),
  production_decision: z.enum(["pending", "use", "mask", "exclude"]),
  masked_path: z.string().nullable().optional(),
  raw_fact_id: z.string().nullable().optional(),
});
export type Media = z.infer<typeof Media>;

export const Gap = z.looseObject({
  id: z.string(),
  item: z.string(),
  guidance: z.string().nullable().optional(),
  review_required: z.boolean().optional(),
  auto_generate: z.boolean().optional(),
});
export type Gap = z.infer<typeof Gap>;

export const GroundTruth = z.looseObject({
  final_dx: z.record(z.string(), z.unknown()),
  accepted_differential: z.unknown().optional(),
  red_herrings: z.unknown().optional(),
  key_discriminators: z.unknown().optional(),
  rubric: z.unknown().optional(),
  get must_do() {
    return ScoredItems.optional();
  },
  get must_not_do() {
    return ScoredItems.optional();
  },
  efficient_path: z.unknown().optional(),
  teaching_points: z.unknown().optional(),
  treatment_given: z.string().nullable().optional(),
  outcome: z.string().nullable().optional(),
});
export type GroundTruth = z.infer<typeof GroundTruth>;

/** Schema 0.3 items are {text, if}; plain strings remain valid for schema 0.2 imports. */
export const ScoredItems = z
  .array(
    z.union([
      z.string(),
      z.looseObject({
        text: z.string(),
        get if() {
          return Condition.optional();
        },
      }),
    ]),
  )
  .nullable();
export type ScoredItems = z.infer<typeof ScoredItems>;

/** SPEC §10.4. Ids ending in .* match every item with that prefix. */
export const Condition = z
  .strictObject({
    get dx_in() {
      return Ids.optional();
    },
    get evidence_has() {
      return Ids.optional();
    },
    get released_all() {
      return Ids.optional();
    },
    get released_any() {
      return Ids.optional();
    },
    get finding_released() {
      return Ids.optional();
    },
    get from_tests() {
      return Ids.optional();
    },
    get asked_any() {
      return Ids.optional();
    },
    get ordered_any() {
      return Ids.optional();
    },
    get ordered_all() {
      return Ids.optional();
    },
    get referred_any() {
      return Ids.optional();
    },
    get plan_has() {
      return Ids.optional();
    },
    get plan_has_any() {
      return Ids.optional();
    },
    plan_before: z.tuple([z.string(), z.string()]).optional(),
    get not() {
      return Condition.optional();
    },
    get all() {
      return z.array(Condition).min(1).optional();
    },
    get any() {
      return z.array(Condition).min(1).optional();
    },
  })
  .superRefine(
    (value, ctx) => {
      const count = Object.keys(value).length;
      if (count < 1 || count > 2) {
        ctx.addIssue({
          code: "custom",
          message: `expected 1 to 2 properties, found ${count}`,
        });
      }
      if ("from_tests" in value && !("finding_released" in value)) {
        ctx.addIssue({
          code: "custom",
          path: ["finding_released"],
          message: 'required when "from_tests" is present',
        });
      }
    },
    {
      when: ({ value }) =>
        typeof value === "object" && value !== null && !Array.isArray(value),
    },
  );
export type Condition = z.infer<typeof Condition>;

export const ConditionOrNull = Condition.nullable();
export type ConditionOrNull = z.infer<typeof ConditionOrNull>;

export const Ids = z.array(z.string()).min(1);
export type Ids = z.infer<typeof Ids>;

export const TestUtility = z.looseObject({
  test_item_id: z.string(),
  utility: z.enum([
    "essential",
    "supportive",
    "low_yield",
    "unnecessary",
    "risky",
  ]),
  rationale: z.string().nullable().optional(),
});
export type TestUtility = z.infer<typeof TestUtility>;

export const Path = z.looseObject({
  path_id: z.string(),
  kind: z.enum(["efficient", "trap", "alternative"]),
  name: z.string(),
  rationale: z.string().nullable().optional(),
  items: z.array(z.string()),
});
export type Path = z.infer<typeof Path>;

/** A frozen case version with its approved results for one catalogue version (Case Library SPEC §10.5). Part of the shared contract: a MINOR version adds optional fields only. Engines load bundles on a server; a bundle never reaches a player's device. */
export const CaseBundle = z.looseObject({
  bundle_id: z
    .string()
    .regex(new RegExp("^(PMC[0-9]+|NID-[0-9]{4,})@v[0-9]+\\.r[0-9]+$")),
  schema_version: z.literal("0.3"),
  catalogue_version: z.number().int().min(0),
  case: z.looseObject({
    slug: z.string().regex(new RegExp("^c-[a-z0-9]{5}$")).optional(),
    display_title: z.string().optional(),
    display_tags: z.array(z.string()).optional(),
    specialty: z.string().optional(),
    difficulty: z.string().optional(),
    est_minutes: z.number().int().min(1).optional(),
    lab_profile: z.record(z.string(), z.unknown()).optional(),
  }),
  source: z
    .looseObject({
      citation: z.string().optional(),
      doi: z.string().optional(),
      pmcid: z.string().regex(new RegExp("^PMC[0-9]+$")).optional(),
      url: z.string().optional(),
      licence: z.string(),
      attribution: z.string().optional(),
      production_ok: z.boolean(),
      public_release_ok: z.boolean(),
    })
    .nullable(),
  clock: z.looseObject({
    day_0: z.iso.date().optional(),
    day_0_label: z.string().optional(),
  }),
  vignette: z.string().nullable(),
  opening_statement_lay: z.string().nullable(),
  get facts() {
    return z.array(Fact);
  },
  get ledger() {
    return z.array(LedgerRow);
  },
  get reports() {
    return z.array(Report);
  },
  get consult_notes() {
    return z.array(ConsultNote);
  },
  get raw_material() {
    return z.array(RawMaterial);
  },
  get media() {
    return z.array(Media);
  },
  get gaps() {
    return z.array(Gap);
  },
  get ground_truth() {
    return GroundTruth;
  },
  get test_utility() {
    return z.array(TestUtility);
  },
  get path_analysis() {
    return z.array(Path);
  },
});
export type CaseBundle = z.infer<typeof CaseBundle>;

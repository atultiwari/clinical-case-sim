import { z } from "zod";

/**
 * The catalogue export: the document `scripts.catalogue build` writes in the Case Library
 * (case-library/scripts/catalogue.py, `build_document`) and the Case Vault loads. Rules as in
 * case-library/catalogue/README.md.
 */

const ID_PATTERNS = {
  history: /^HX\.[A-Z0-9_.]+$/,
  exam: /^EX\.[A-Z0-9_.]+$/,
  test: /^(LAB|IMG|PROC)\.[A-Z0-9_.]+$/,
  action: /^(RX|ACT)\.[A-Z0-9_.]+$/,
  referral: /^REF\.[A-Z0-9_.]+$/,
  diagnosis: /^DX\.[A-Z0-9_.]+$/,
  finding: /^FND\.[A-Z0-9_.]+$/,
} as const;

export const CatalogueItemKind = z.enum([
  "history",
  "exam",
  "test",
  "action",
  "referral",
  "diagnosis",
  "finding",
]);
export type CatalogueItemKind = z.infer<typeof CatalogueItemKind>;

const ComponentId = z
  .string()
  .regex(/^CMP\.[A-Z0-9_.]+$/, "expected a component id (CMP.*)");
const TestId = z
  .string()
  .regex(ID_PATTERNS.test, "expected a test id (LAB.*, IMG.* or PROC.*)");

export const CatalogueItem = z
  .object({
    id: z.string(),
    kind: CatalogueItemKind,
    name: z.string().min(1),
    category: z.string(),
    synonyms: z.array(z.string()),
    specialty_scope: z.array(z.string()),
  })
  .superRefine((item, ctx) => {
    const pattern = ID_PATTERNS[item.kind];
    if (!pattern.test(item.id)) {
      ctx.addIssue({
        code: "custom",
        path: ["id"],
        message: `"${item.id}" does not fit the ${item.kind} pattern ${pattern.source}`,
      });
    }
  });
export type CatalogueItem = z.infer<typeof CatalogueItem>;

export const TestRoute = z.enum([
  "direct",
  "service.pathology",
  "service.radiology",
  "service.microbiology",
]);
export type TestRoute = z.infer<typeof TestRoute>;

export const CatalogueTest = z.object({
  item_id: TestId,
  route: TestRoute,
  specimen: z.string().nullable(),
  price_inr: z.number().min(0).nullable(),
  price_source: z.string(),
  tat_minutes: z.number().min(0).nullable(),
  invasive: z.boolean(),
  loinc: z.string().nullable(),
  components: z.array(ComponentId).min(1),
});
export type CatalogueTest = z.infer<typeof CatalogueTest>;

export const ReferenceRange = z.object({
  sex: z.enum(["F", "M", "any"]),
  age_min: z.number().optional(),
  age_max: z.number().optional(),
  low: z.number().optional(),
  high: z.number().optional(),
  text: z.string().optional(),
  display: z.string().optional(),
  source: z.string(),
});
export type ReferenceRange = z.infer<typeof ReferenceRange>;

export const CatalogueComponent = z.object({
  id: ComponentId,
  name: z.string().min(1),
  loinc: z.string().nullable(),
  unit_si: z.string().nullable(),
  unit_conv: z.string().nullable(),
  conv_factor: z.number().nullable(),
  decimals: z.number().int().min(0).nullable(),
  ref_ranges: z.array(ReferenceRange),
  normal_text: z.string().nullable(),
});
export type CatalogueComponent = z.infer<typeof CatalogueComponent>;

export const NormalTemplate = z.object({
  item_id: z.string(),
  template: z.string(),
  review_status: z.enum(["pending", "approved"]),
});
export type NormalTemplate = z.infer<typeof NormalTemplate>;

export const DiagnosisCodes = z.object({
  item_id: z
    .string()
    .regex(ID_PATTERNS.diagnosis, "expected a diagnosis id (DX.*)"),
  icd11: z.string().nullable(),
  icd10: z.string().nullable(),
});
export type DiagnosisCodes = z.infer<typeof DiagnosisCodes>;

export const ValueRule = z.object({
  id: z.string(),
  kind: z.enum(["ratio", "difference", "not_above", "sum_equals"]),
  target: ComponentId,
  inputs: z.array(ComponentId).min(1),
  factor: z.number(),
  tolerance_pct: z.number().min(0),
  formula: z.string(),
});
export type ValueRule = z.infer<typeof ValueRule>;

export const CatalogueExport = z.object({
  version: z.number().int().min(0),
  items: z.array(CatalogueItem),
  tests: z.array(CatalogueTest),
  components: z.array(CatalogueComponent),
  normal_templates: z.array(NormalTemplate),
  diagnoses: z.array(DiagnosisCodes),
  value_rules: z.array(ValueRule),
});
export type CatalogueExport = z.infer<typeof CatalogueExport>;

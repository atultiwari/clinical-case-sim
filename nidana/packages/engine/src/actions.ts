import { z } from "zod";

/** One player action (SPEC §5.2 and §5.12). */

const ItemId = z.string().min(1);

const distinct = (ids: readonly string[]): boolean =>
  new Set(ids).size === ids.length;
const Distinct = { message: "each item may appear only once" };

export const MAX_EVIDENCE = 5;

export const Action = z.discriminatedUnion("kind", [
  z.strictObject({ kind: z.literal("ask"), item: ItemId }),
  z.strictObject({ kind: z.literal("examine"), item: ItemId }),
  z.strictObject({ kind: z.literal("order"), item: ItemId }),
  z.strictObject({ kind: z.literal("refer"), item: ItemId }),
  /** Without minutes: until the next due result, or the start of the next day if none is due. */
  z.strictObject({
    kind: z.literal("wait"),
    minutes: z.number().int().positive().optional(),
  }),
  /** The player's ranked differential, most likely first. */
  z.strictObject({
    kind: z.literal("differential"),
    items: z.array(ItemId).min(1).max(10),
  }),
  /** Ends the encounter: a diagnosis, up to five released items as key evidence, and a plan of actions and referrals in order. */
  z.strictObject({
    kind: z.literal("commit"),
    dx: ItemId,
    evidence: z.array(ItemId).max(MAX_EVIDENCE).refine(distinct, Distinct),
    plan: z.array(ItemId).max(30).refine(distinct, Distinct),
    /** Free-text reasoning; stored, not scored before the voice mode. */
    note: z.string().max(2000).optional(),
  }),
]);
export type Action = z.infer<typeof Action>;

export type ItemAction = Extract<Action, { item: string }>;

/** The catalogue kind each item action takes. */
export const ACTION_ITEM_KIND = {
  ask: "history",
  examine: "exam",
  order: "test",
  refer: "referral",
} as const satisfies Record<ItemAction["kind"], string>;

/** The seat Nidana's player takes in Phase 1 (Sambhasha's id). */
export const SEAT = "attending";

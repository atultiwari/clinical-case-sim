import { z } from "zod";

/** One player action (SPEC §5.2). Commit is added with scoring (N1.3). */

const ItemId = z.string().min(1);

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

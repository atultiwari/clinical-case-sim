import { describe, expect, it } from "vitest";
import { z } from "zod";
import {
  Action,
  Difficulty,
  prepareCase,
  releasedIds,
  replay,
  valueOf,
} from "../src/index.ts";
import { catalogue, loadBundle, readConformance, settings } from "./helpers.ts";

const Playthrough = z.object({
  description: z.string(),
  bundle: z.string(),
  difficulty: Difficulty,
  actions: z.array(Action),
  expect: z.object({
    clock: z.number(),
    spend: z.number(),
    released: z.array(z.string()),
    not_released: z.array(z.string()),
    values: z.record(z.string(), z.string()),
    pending: z.array(z.string()),
  }),
});

describe.each(["PMC12949993/benchmark-path.json"])("conformance %s", (file) => {
  const playthrough = Playthrough.parse(readConformance(file));
  const prepared = prepareCase(loadBundle(playthrough.bundle), catalogue);
  const state = replay(
    prepared,
    settings,
    playthrough.difficulty,
    playthrough.actions,
  );
  const { expect: expected } = playthrough;

  it("ends at the expected time and spend", () => {
    expect(state.clock).toBe(expected.clock);
    expect(state.spend).toBe(expected.spend);
    expect(state.pending.map((p) => p.item)).toEqual(expected.pending);
  });

  it("releases what it should and nothing it should not", () => {
    const ids = releasedIds(state);
    expect(expected.released.filter((id) => !ids.has(id))).toEqual([]);
    expect(expected.not_released.filter((id) => ids.has(id))).toEqual([]);
  });

  it("shows the expected values", () => {
    for (const [component, value] of Object.entries(expected.values)) {
      expect(valueOf(prepared, state, component)?.value).toBe(value);
    }
  });
});

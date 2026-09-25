"use client";

import { useActionState, useState } from "react";

import type { ActionState } from "@/lib/action-state";
import { FIGURE_DECISIONS, type FigureDecisionValue } from "@/lib/review-input";
import { submitFigureDecision } from "@/server/actions/decisions";

type Props = {
  caseVersionId: string;
  caseId: string;
  mediaId: string;
  current: string;
  currentMaskedPath: string | null;
};

const LABELS = { use: "Use", mask: "Mask", exclude: "Exclude" } as const;

function initialDecision(current: string): FigureDecisionValue {
  return (FIGURE_DECISIONS as readonly string[]).includes(current) ? (current as FigureDecisionValue) : "use";
}

/** Use, mask (with the masked copy's path in case-media) or exclude one figure (SPEC §9). */
export function FigureDecisionForm({ caseVersionId, caseId, mediaId, current, currentMaskedPath }: Props) {
  const [state, action, pending] = useActionState<ActionState, FormData>(submitFigureDecision, null);
  const [decision, setDecision] = useState<FigureDecisionValue>(initialDecision(current));
  return (
    <form action={action} className="space-y-1 rounded-md border bg-neutral-50 p-2 text-xs">
      <input type="hidden" name="caseVersionId" value={caseVersionId} />
      <input type="hidden" name="mediaId" value={mediaId} />
      <div className="flex flex-wrap gap-2">
        <span className="text-muted-foreground">Production decision:</span>
        {FIGURE_DECISIONS.map((value) => (
          <label key={value} className="inline-flex items-center gap-1">
            <input type="radio" name="decision" value={value} checked={decision === value} onChange={() => setDecision(value)} />
            {LABELS[value]}
          </label>
        ))}
      </div>
      {decision === "mask" ? (
        <label className="block">
          <span className="text-muted-foreground">Masked copy in case-media (cropped or covered by ordinary editing, never AI)</span>
          <input
            name="maskedPath"
            required
            defaultValue={currentMaskedPath ?? `${caseId}/${mediaId}-masked.png`}
            maxLength={200}
            className="w-full rounded-md border bg-white px-1 py-0.5 font-mono"
          />
        </label>
      ) : null}
      <button type="submit" disabled={pending} className="rounded-md border bg-white px-2 py-0.5 hover:bg-muted disabled:opacity-50">
        {pending ? "Saving…" : "Record figure decision"}
      </button>
      {state ? (
        <p role="status" className={state.ok ? "text-emerald-800" : "text-red-700"}>
          {state.message}
        </p>
      ) : null}
    </form>
  );
}

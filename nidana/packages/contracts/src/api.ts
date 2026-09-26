/**
 * The game server's HTTP API (nidana/docs/SPEC.md §6.2–6.3): the shapes the player app sends
 * and receives. Types only; nothing here holds case content. The server builds these from the
 * engine's state and checks the correspondence with type tests.
 */

export type Difficulty = "guided" | "standard" | "expert";

/** Every response: `{ success, data, error }`. */
export interface Envelope<T> {
  readonly success: boolean;
  readonly data: T | null;
  readonly error: { readonly code: string; readonly message: string } | null;
}

/** GET /api/cases */
export interface CaseCard {
  readonly slug: string;
  readonly title: string;
  readonly tags: readonly string[];
  readonly specialty: string | null;
  readonly difficulty: string | null;
  readonly estMinutes: number | null;
}

/** GET /api/catalogue */
export interface SearchItem {
  readonly id: string;
  readonly kind: string;
  readonly name: string;
  readonly category: string;
  readonly synonyms: readonly string[];
  readonly priceInr?: number | null;
  readonly turnaroundMinutes?: number | null;
}

/** POST /api/encounters */
export interface StartRequest {
  readonly slug: string;
  readonly difficulty: Difficulty;
}

/** POST /api/encounters/:id/actions */
export type ActionRequest =
  | {
      readonly kind: "ask" | "examine" | "order" | "refer";
      readonly item: string;
    }
  | { readonly kind: "wait"; readonly minutes?: number }
  | { readonly kind: "differential"; readonly items: readonly string[] };

export type EntryKind =
  | "vignette"
  | "history"
  | "exam"
  | "result"
  | "report"
  | "consult"
  | "no_record";

export interface ResultValue {
  readonly value: string;
  readonly unit: string | null;
  readonly refRange: string | null;
  readonly flag: string | null;
  /** For the units toggle: conventional unit, SI × factor, and decimals (N-019). */
  readonly conventional: {
    readonly unit: string;
    readonly factor: number;
    readonly decimals: number | null;
  } | null;
}

export interface ReportContent {
  readonly status: "provisional" | "final";
  readonly statusLine: string | null;
  readonly text: string | null;
  readonly impression: string | null;
  readonly suggestedTests: readonly string[];
}

export interface ChartEntry {
  /** Cite this as evidence at commit (`c0`, `c1`, …). */
  readonly ref: string;
  readonly at: number;
  readonly kind: EntryKind;
  readonly item: string | null;
  readonly itemName: string | null;
  /** The day the value was taken, when it differs from the day asked for ("result from day 0"). */
  readonly takenDay: number | null;
  readonly requestedDay: number | null;
  readonly component: { readonly id: string; readonly name: string } | null;
  readonly text: string | null;
  readonly value: ResultValue | null;
  readonly report: ReportContent | null;
  readonly recommendations: readonly string[];
}

export interface PendingItem {
  readonly item: string;
  readonly itemName: string | null;
  readonly kind: "order" | "referral";
  readonly orderedAt: number;
  readonly dueAt: number;
}

/** GET /api/encounters/:id/view, and the reply to every action. */
export interface PlayerView {
  readonly encounterId: string;
  readonly status: "active" | "committed";
  readonly difficulty: Difficulty;
  readonly case: {
    readonly slug: string;
    readonly title: string;
    readonly tags: readonly string[];
    readonly specialty: string | null;
    readonly vignette: string | null;
    readonly openingStatement: string | null;
  };
  readonly clock: number;
  readonly day: number;
  readonly spend: number;
  readonly limits: {
    readonly budget: number;
    readonly budgetLeft: number;
    readonly maxStayMinutes: number;
    readonly referralsAllowed: number;
    readonly referralsUsed: number;
  };
  readonly mustCommit: "max_stay" | null;
  readonly chart: readonly ChartEntry[];
  readonly pending: readonly PendingItem[];
  readonly differential: readonly {
    readonly at: number;
    readonly items: readonly string[];
  }[];
}

/** POST /api/encounters/:id/commit */
export interface CommitRequest {
  readonly dx: string;
  /** Chart references, at most five. */
  readonly evidence: readonly string[];
  /** Action and referral items, in the order they should happen. */
  readonly plan: readonly string[];
  readonly note?: string;
}

export interface CommitResult {
  readonly total: number;
  readonly diagnosisAnchor: number;
  readonly scoringVersion: string;
}

/** POST /api/missing */
export interface MissingRequest {
  readonly encounterId: string;
  readonly kind:
    "history" | "exam" | "test" | "referral" | "action" | "diagnosis";
  readonly query: string;
}

export interface RuleOutcomeView {
  readonly text: string;
  readonly met: boolean | null;
}

export interface ScoreView {
  readonly version: string;
  readonly total: number;
  readonly diagnosis: {
    readonly anchor: number;
    readonly text: string | null;
    readonly points: number;
  };
  readonly management: {
    readonly points: number;
    readonly met: number;
    readonly scorable: number;
  };
  readonly mustDo: readonly RuleOutcomeView[];
  readonly efficiency: {
    readonly points: number;
    readonly cost: number;
    readonly tests: number;
    readonly time: number;
  };
  readonly reasoning: {
    readonly points: number;
    readonly differential: number;
    readonly discriminators: number;
    readonly referrals: number;
  };
  readonly safety: {
    readonly violations: readonly { readonly text: string }[];
    readonly penalty: number;
    readonly capApplied: boolean;
  };
}

export type Origin =
  | "article"
  | "derived"
  | "affected"
  | "normal"
  | "rule"
  | "reviewer"
  | "unknown";

/** GET /api/encounters/:id/debrief: only after the commit (SPEC §5.13). */
export interface DebriefView {
  readonly finalDiagnosis: { readonly id: string; readonly name: string };
  readonly committed: {
    readonly dx: { readonly id: string; readonly name: string };
    readonly evidence: readonly string[];
    readonly plan: readonly { readonly id: string; readonly name: string }[];
    readonly at: number;
  };
  readonly score: ScoreView;
  readonly paths: {
    readonly player: readonly { readonly id: string; readonly name: string }[];
    readonly efficient: readonly {
      readonly id: string;
      readonly name: string;
      readonly done: boolean;
    }[];
    readonly spend: number;
    readonly efficientCost: number;
  };
  /** The origin of every Chart entry, by reference: revealed only now (invariant I4). */
  readonly origins: Readonly<Record<string, Origin>>;
  readonly reports: readonly {
    readonly test: string;
    readonly testName: string;
    readonly provisional: ReportContent;
    readonly final: ReportContent | null;
    readonly finalSeen: boolean;
  }[];
  readonly keyDiscriminators: readonly string[];
  readonly teachingPoints: readonly string[];
  readonly acceptedDifferential: readonly string[];
  readonly redHerrings: readonly string[];
  readonly source: {
    readonly citation: string | null;
    readonly doi: string | null;
    readonly url: string | null;
    readonly licence: string;
    readonly attribution: string | null;
  } | null;
}

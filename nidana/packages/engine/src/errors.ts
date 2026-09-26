export type EngineErrorCode =
  | "invalid_settings"
  | "catalogue_mismatch"
  | "no_efficient_path"
  | "invalid_action"
  | "unknown_item"
  | "wrong_kind"
  | "not_available_to_seat"
  | "over_budget"
  | "referral_limit"
  | "must_commit";

/** A refusal the server can show or log. `code` is stable; `message` is for people. */
export interface ActionError {
  readonly code: EngineErrorCode;
  readonly message: string;
}

export class EngineError extends Error {
  readonly code: EngineErrorCode;

  constructor(code: EngineErrorCode, message: string) {
    super(message);
    this.name = "EngineError";
    this.code = code;
  }
}

import type { z } from "zod";
import { CatalogueExport } from "./catalogue.ts";
import { CaseBundle } from "./generated/case-bundle.ts";

export interface ContractIssue {
  /** Where the problem is, for example `facts[3].origin`; empty for the whole document. */
  readonly path: string;
  readonly message: string;
}

export interface ContractError {
  /** One readable paragraph: what was checked, how many problems, and each one on its own line. */
  readonly message: string;
  readonly issues: readonly ContractIssue[];
}

export type ParseResult<T> =
  | { readonly success: true; readonly data: T; readonly error: null }
  | {
      readonly success: false;
      readonly data: null;
      readonly error: ContractError;
    };

type Issue = z.core.$ZodIssue;
type PathKey = PropertyKey;

export function formatPath(path: readonly PathKey[]): string {
  return path
    .map((key, i) => {
      if (typeof key === "number") return `[${key}]`;
      const name = String(key);
      return i === 0 ? name : `.${name}`;
    })
    .join("");
}

/** True when a union branch failed only because the value has another JSON type. */
function isTypeMismatch(issues: readonly Issue[]): boolean {
  return issues.every(
    (issue) => issue.code === "invalid_type" && issue.path.length === 0,
  );
}

/**
 * Flattens Zod issues into path and message pairs. For a union (a scored item is a string or an
 * object, say), it reports the problems of the branch whose type matched, not "invalid input".
 */
function flatten(
  issues: readonly Issue[],
  prefix: readonly PathKey[],
): ContractIssue[] {
  return issues.flatMap((issue) => {
    const path = [...prefix, ...issue.path];
    if (issue.code === "invalid_union" && issue.errors.length > 0) {
      const matching = issue.errors.filter((branch) => !isTypeMismatch(branch));
      if (matching.length > 0)
        return matching.flatMap((branch) => flatten(branch, path));
    }
    return [{ path: formatPath(path), message: issue.message }];
  });
}

function describeIssues(
  what: string,
  issues: readonly ContractIssue[],
): string {
  const count = issues.length === 1 ? "1 problem" : `${issues.length} problems`;
  const lines = issues.map(
    (issue) => `- ${issue.path || "(document)"}: ${issue.message}`,
  );
  return [`Invalid ${what} (${count}):`, ...lines].join("\n");
}

function failure<T>(
  message: string,
  issues: readonly ContractIssue[],
): ParseResult<T> {
  return { success: false, data: null, error: { message, issues } };
}

function parseWith<T>(
  schema: z.ZodType<T>,
  what: string,
  input: unknown,
): ParseResult<T> {
  const result = schema.safeParse(input);
  if (result.success) return { success: true, data: result.data, error: null };
  const issues = flatten(result.error.issues, []);
  return failure(describeIssues(what, issues), issues);
}

function parseJsonWith<T>(
  parse: (input: unknown) => ParseResult<T>,
  what: string,
  text: string,
): ParseResult<T> {
  let input: unknown;
  try {
    input = JSON.parse(text);
  } catch (error: unknown) {
    const detail = error instanceof Error ? error.message : String(error);
    return failure(`The ${what} is not valid JSON: ${detail}`, [
      { path: "", message: detail },
    ]);
  }
  return parse(input);
}

/** Checks a case bundle against schema 0.3. It does not check the pinned catalogue version. */
export function parseBundle(input: unknown): ParseResult<CaseBundle> {
  return parseWith(CaseBundle, "case bundle", input);
}

export function parseBundleJson(text: string): ParseResult<CaseBundle> {
  return parseJsonWith(parseBundle, "case bundle", text);
}

export function parseCatalogue(input: unknown): ParseResult<CatalogueExport> {
  return parseWith(CatalogueExport, "catalogue export", input);
}

export function parseCatalogueJson(text: string): ParseResult<CatalogueExport> {
  return parseJsonWith(parseCatalogue, "catalogue export", text);
}

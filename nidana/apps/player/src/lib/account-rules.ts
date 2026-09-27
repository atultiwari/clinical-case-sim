/** Account rules shared by the consent and profile screens (N1.6). */

export const TRAINING_LEVELS = [
  { value: "mbbs_student", label: "MBBS student" },
  { value: "intern", label: "Intern" },
  { value: "resident", label: "Resident" },
  { value: "consultant", label: "Consultant" },
  { value: "other", label: "Other" },
] as const;

/** The same rule the server applies: 2–24 characters; letters, digits, spaces and . _ ' - only. */
export function nicknameProblem(nickname: string): string | null {
  const trimmed = nickname.trim();
  if (trimmed.length < 2 || trimmed.length > 24)
    return "Use 2 to 24 characters.";
  if (!/^[\p{L}\p{N} ._'-]+$/u.test(trimmed))
    return "Use letters, digits, spaces and . _ ' - only.";
  return null;
}

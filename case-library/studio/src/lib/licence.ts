import type { Tone } from "@/lib/status";

export type LicenceFlags = {
  licence: string | null;
  production_ok: boolean | null;
  public_release_ok: boolean | null;
};

export type LicenceBadge = { label: string; tone: Tone; title: string };

/** NC or ND in a Creative Commons licence name (SPEC §9). */
export function hasNcOrNd(licence: string | null): boolean {
  if (!licence) return false;
  return /(^|[^A-Z])(NC|ND)([^A-Z]|$)/.test(licence.toUpperCase());
}

/**
 * Badges for a case or a figure (SPEC §8, §9): red "Development only" when the
 * store release is not allowed (production_ok false, as for NC and ND
 * licences); "Public release" when public_release_ok. A flag that contradicts
 * the licence name is shown too, so it can be corrected.
 */
export function licenceBadges(flags: LicenceFlags): LicenceBadge[] {
  const badges: LicenceBadge[] = [];
  const productionOk = flags.production_ok === true;
  if (!productionOk) {
    badges.push({
      label: "Development only",
      tone: "danger",
      title: "production_ok is false: not for the store release",
    });
  } else {
    badges.push({ label: "Production", tone: "success", title: "production_ok is true" });
  }
  if (flags.public_release_ok === true) {
    badges.push({ label: "Public release", tone: "info", title: "public_release_ok is true" });
  }
  if (productionOk && hasNcOrNd(flags.licence)) {
    badges.push({
      label: "Check flags",
      tone: "warning",
      title: `${flags.licence ?? ""} has NC or ND but production_ok is true`,
    });
  }
  return badges;
}

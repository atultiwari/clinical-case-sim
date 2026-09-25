/** Row shapes shared by the queries (src/server/queries) and the pure helpers. */

export type FactRow = {
  id: string;
  category: string;
  item: string;
  catalogue_ref: string | null;
  value: string | null;
  value_num: number | null;
  unit: string | null;
  ref_range: string | null;
  flag: string | null;
  day: number | null;
  kind: string;
  origin: string;
  formula: string | null;
  reveals_dx: boolean;
  pivotal: boolean;
  release: string;
  source_locator: string | null;
  review_status: string;
};

export type SeriesPoint = { day: number; value: number; flag: string | null };

-- Sambhasha: what the Synthetic Findings Service needs to keep per generated row (PLAN P1.4).
-- The request as written, the catalogue kinds it was coded against, the gap it matched, and
-- the result text itself. `code` holds "REQ:" plus the normalised request.

alter table sambhasha.synthetic_ledger
  add column query text not null,
  add column kind text not null,
  add column gap_id text,
  add column result_text text not null;

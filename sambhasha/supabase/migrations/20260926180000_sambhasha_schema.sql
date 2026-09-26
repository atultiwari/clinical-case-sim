-- Sambhasha's run database (SPEC §12; PLAN P0.3).
--
-- Case tables hold imported Case Library bundles (schema 0.3). Each row keeps its typed key
-- columns for queries and the whole row, as the bundle carried it, in `data`; `pos` keeps
-- the bundle's order. A bundle is sealed when its import finishes: from then on nothing in it
-- can be inserted, changed or deleted (invariant I7). Eligibility for a study's primary
-- results is kept apart, because it changes with the Case Library's notices.
--
-- Run tables hold runs, the Event Log (insert-only, invariant I6), orders and scores.

create schema sambhasha;

-- --- cases ---

create table sambhasha.case_bundle (
  bundle_id text primary key check (bundle_id ~ '^(PMC[0-9]+|NID-[0-9]{4,})@v[0-9]+\.r[0-9]+$'),
  case_version_id text not null,
  revision int not null check (revision >= 1),
  schema_version text not null,
  catalogue_version int not null check (catalogue_version >= 0),
  sha256 text not null check (sha256 ~ '^[0-9a-f]{64}$'),
  head jsonb not null,            -- case, source, clock, vignette and opening statement
  imported_at timestamptz not null default now(),
  sealed_at timestamptz,
  unique (case_version_id, revision),
  check (bundle_id = case_version_id || '.r' || revision)
);

create table sambhasha.bundle_eligibility (
  bundle_id text primary key references sambhasha.case_bundle (bundle_id),
  primary_eligible boolean not null default false,
  reason text not null,
  decided_at timestamptz not null default now()
);

create table sambhasha.fact (
  bundle_id text not null references sambhasha.case_bundle (bundle_id),
  id text not null,
  pos int not null,
  category text not null,
  item text not null,
  catalogue_ref text,
  day int,
  release text not null,
  origin text not null check (origin in ('article', 'derived')),
  data jsonb not null,
  primary key (bundle_id, id),
  unique (bundle_id, pos)
);
create index fact_catalogue_ref on sambhasha.fact (bundle_id, catalogue_ref);

create table sambhasha.ledger_row (
  bundle_id text not null references sambhasha.case_bundle (bundle_id),
  id text not null,
  pos int not null,
  target text not null,
  day_bucket int,
  tier text not null check (tier in ('affected', 'normal', 'rule', 'reviewer')),
  data jsonb not null,
  primary key (bundle_id, id),
  unique (bundle_id, pos)
);
create index ledger_row_target on sambhasha.ledger_row (bundle_id, target, day_bucket);

create table sambhasha.report (
  bundle_id text not null references sambhasha.case_bundle (bundle_id),
  id text not null,
  pos int not null,
  test_item_id text,
  variant text not null,
  status text not null,
  data jsonb not null,
  primary key (bundle_id, id),
  unique (bundle_id, pos)
);

create table sambhasha.consult_note (
  bundle_id text not null references sambhasha.case_bundle (bundle_id),
  id text not null,
  pos int not null,
  specialty text not null,
  variant int not null,
  data jsonb not null,
  primary key (bundle_id, id),
  unique (bundle_id, pos)
);

create table sambhasha.raw_material (
  bundle_id text not null references sambhasha.case_bundle (bundle_id),
  id text not null,
  pos int not null,
  test text not null,
  release text not null,
  day int,
  data jsonb not null,
  primary key (bundle_id, id),
  unique (bundle_id, pos)
);

create table sambhasha.media (
  bundle_id text not null references sambhasha.case_bundle (bundle_id),
  id text not null,
  pos int not null,
  data jsonb not null,
  primary key (bundle_id, id),
  unique (bundle_id, pos)
);

create table sambhasha.gap (
  bundle_id text not null references sambhasha.case_bundle (bundle_id),
  id text not null,
  pos int not null,
  item text not null,
  auto_generate boolean not null,
  data jsonb not null,
  primary key (bundle_id, id),
  unique (bundle_id, pos)
);

create table sambhasha.test_utility (
  bundle_id text not null references sambhasha.case_bundle (bundle_id),
  test_item_id text not null,
  pos int not null,
  utility text not null,
  data jsonb not null,
  primary key (bundle_id, test_item_id),
  unique (bundle_id, pos)
);

create table sambhasha.path_analysis (
  bundle_id text not null references sambhasha.case_bundle (bundle_id),
  path_id text not null,
  pos int not null,
  kind text not null,
  data jsonb not null,
  primary key (bundle_id, path_id),
  unique (bundle_id, pos)
);

-- The ground truth: only the Synthetic Findings Service and the Evaluator read it (I8).
create table sambhasha.ground_truth (
  bundle_id text primary key references sambhasha.case_bundle (bundle_id),
  data jsonb not null
);

-- Out-of-catalogue results generated during runs (SPEC §8; D-023). Filled in P1.4.
create table sambhasha.synthetic_ledger (
  id uuid primary key default gen_random_uuid(),
  bundle_id text not null references sambhasha.case_bundle (bundle_id),
  code text not null,
  day_bucket int,
  value jsonb,
  narrative text,
  rationale text,
  confidence numeric check (confidence between 0 and 1),
  checks jsonb,
  generator_model text not null,
  prompt_version text not null,
  review_status text not null default 'pending'
    check (review_status in ('pending', 'approved', 'edited', 'rejected')),
  reviewed_by text,
  created_at timestamptz not null default now(),
  unique nulls not distinct (bundle_id, code, day_bucket)
);

-- --- runs ---

create table sambhasha.run (
  id uuid primary key,
  bundle_id text not null references sambhasha.case_bundle (bundle_id),
  engine_version text not null,
  config_hash text not null check (config_hash ~ '^[0-9a-f]{64}$'),
  started_at timestamptz not null,
  ended_at timestamptz,
  status text not null check (status in ('running', 'completed', 'aborted'))
);

create table sambhasha.event (
  id bigint generated always as identity primary key,
  run_id uuid not null references sambhasha.run (id),
  seq int not null check (seq >= 0),
  sim_minutes int not null check (sim_minutes >= 0),
  seat text not null,
  type text not null,
  payload jsonb not null,
  visibility text[] not null,
  source text not null check (source in ('article', 'synthetic', 'seat', 'engine')),
  model text,
  prompt_version text,
  tokens_in int check (tokens_in >= 0),
  tokens_out int check (tokens_out >= 0),
  cost_usd numeric check (cost_usd >= 0),
  hash text,
  recorded_at timestamptz not null default now(),
  unique (run_id, seq)
);

create table sambhasha."order" (
  id uuid primary key,
  run_id uuid not null references sambhasha.run (id),
  ordered_by text not null,
  item_text text not null,
  code text,
  indication text not null,
  route text not null
    check (route in ('direct', 'service.pathology', 'service.radiology', 'service.microbiology')),
  status text not null check (status in ('placed', 'resulted', 'reported', 'cancelled')),
  cost_inr numeric not null check (cost_inr >= 0),
  ordered_at_min int not null check (ordered_at_min >= 0),
  due_at_min int not null check (due_at_min >= ordered_at_min)
);
create index order_run on sambhasha."order" (run_id);

create table sambhasha.score (
  id uuid primary key,
  run_id uuid not null references sambhasha.run (id),
  data jsonb not null,            -- the whole score as the domain model holds it
  rater text not null,
  rater_type text not null check (rater_type in ('llm', 'human')),
  dx_score int not null check (dx_score between 1 and 5),
  recorded_at timestamptz not null default now()
);
create index score_run on sambhasha.score (run_id);

-- --- guards ---

-- A sealed bundle's rows cannot be inserted, changed or deleted (invariant I7).
create function sambhasha.guard_sealed_content()
returns trigger
language plpgsql
set search_path = ''
as $$
declare
  v_bundle text := case when tg_op = 'DELETE' then old.bundle_id else new.bundle_id end;
begin
  if tg_op = 'UPDATE' and old.bundle_id is distinct from new.bundle_id then
    raise exception 'sambhasha.%: rows cannot move between bundles', tg_table_name;
  end if;
  if exists (select 1 from sambhasha.case_bundle
             where bundle_id = v_bundle and sealed_at is not null) then
    raise exception 'sambhasha.%: bundle % is sealed; a change means a new bundle revision',
      tg_table_name, v_bundle;
  end if;
  return case when tg_op = 'DELETE' then old else new end;
end
$$;

do $$
declare
  t text;
begin
  foreach t in array array['fact', 'ledger_row', 'report', 'consult_note', 'raw_material',
                           'media', 'gap', 'test_utility', 'path_analysis', 'ground_truth'] loop
    execute format(
      'create trigger guard_sealed_content before insert or update or delete on sambhasha.%I '
      'for each row execute function sambhasha.guard_sealed_content()', t);
  end loop;
end
$$;

-- A bundle row can only be sealed; once sealed it never changes and is never deleted.
create function sambhasha.guard_sealed_bundle()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  if old.sealed_at is not null then
    raise exception 'sambhasha.case_bundle: bundle % is sealed', old.bundle_id;
  end if;
  return case when tg_op = 'DELETE' then old else new end;
end
$$;

create trigger guard_sealed_bundle before update or delete on sambhasha.case_bundle
  for each row execute function sambhasha.guard_sealed_bundle();

-- The Event Log is insert-only (invariant I6).
create function sambhasha.guard_event_log()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  raise exception 'sambhasha.event is insert-only (% refused)', tg_op;
end
$$;

create trigger guard_event_log before update or delete on sambhasha.event
  for each row execute function sambhasha.guard_event_log();
create trigger guard_event_log_truncate before truncate on sambhasha.event
  for each statement execute function sambhasha.guard_event_log();

-- Nothing here is for Supabase's API roles: Sambhasha connects as the database owner.
revoke all on schema sambhasha from anon, authenticated;
revoke all on all tables in schema sambhasha from anon, authenticated;
revoke all on all functions in schema sambhasha from anon, authenticated, public;

-- Case Vault schema 0.3: tables (SPEC §10.1 and §10.2, PLAN L0.3).
-- Triggers, the live-ledger index and the SQL functions come in later migrations.
-- The schema is not exposed through the Data API (config.toml [api].schemas) and
-- RLS is on with no client policies, so only the service role and the MCP reach it.

create schema if not exists casevault;
comment on schema casevault is 'Case Library authoring tables (SPEC §10). Not exposed to the Data API.';

-- ---------------------------------------------------------------------------
-- Catalogues: global and versioned
-- ---------------------------------------------------------------------------

create table casevault.catalogue_item (
  id text primary key,
  kind text not null check (kind in ('history','exam','test','action','referral','diagnosis','finding')),
  name text not null,
  category text,
  synonyms text[] not null default '{}',
  specialty_scope text[] not null default '{}',
  active boolean not null default false,
  since_version int not null check (since_version >= 0),
  check (
    (kind = 'history'   and id ~ '^HX\.[A-Z0-9_.]+$') or
    (kind = 'exam'      and id ~ '^EX\.[A-Z0-9_.]+$') or
    (kind = 'test'      and id ~ '^(LAB|IMG|PROC)\.[A-Z0-9_.]+$') or
    (kind = 'action'    and id ~ '^(RX|ACT)\.[A-Z0-9_.]+$') or
    (kind = 'referral'  and id ~ '^REF\.[A-Z0-9_.]+$') or
    (kind = 'diagnosis' and id ~ '^DX\.[A-Z0-9_.]+$') or
    (kind = 'finding'   and id ~ '^FND\.[A-Z0-9_.]+$')
  )
);

create table casevault.test_def (
  item_id text primary key references casevault.catalogue_item (id),
  route text,
  specimen text,
  price_inr numeric check (price_inr >= 0),
  price_source text,
  tat_minutes int check (tat_minutes >= 0),
  invasive boolean not null default false,
  loinc text
);

create table casevault.component (
  id text primary key check (id ~ '^CMP\.[A-Z0-9_.]+$'),
  name text not null,
  loinc text,
  unit_si text,
  unit_conv text,
  conv_factor numeric,
  decimals int check (decimals between 0 and 6),
  ref_ranges jsonb,
  normal_text text
);

create table casevault.test_component (
  test_item_id text not null references casevault.test_def (item_id),
  component_id text not null references casevault.component (id),
  position int not null check (position >= 1),
  primary key (test_item_id, component_id),
  unique (test_item_id, position)
);

create table casevault.normal_template (
  item_id text primary key references casevault.catalogue_item (id),
  template text not null,
  review_status text not null default 'pending' check (review_status in ('pending','approved','rejected'))
);

create table casevault.diagnosis_def (
  item_id text primary key references casevault.catalogue_item (id),
  icd11 text,
  icd10 text
);

-- ---------------------------------------------------------------------------
-- Sources, cases and case versions
-- ---------------------------------------------------------------------------

create table casevault.source_article (
  id uuid primary key default gen_random_uuid(),
  pmcid text unique check (pmcid ~ '^PMC[0-9]+$'),
  doi text,
  title text not null,
  journal text,
  published date,
  url text,                                    -- schema 0.2
  licence text not null,
  licence_verified_at timestamptz,
  production_ok boolean not null default false,
  public_release_ok boolean not null default false,
  attribution text,
  fulltext_format text,
  fulltext text,
  content_hash text,
  fetched_at timestamptz
);

create table casevault."case" (
  id text primary key check (id ~ '^(PMC[0-9]+|NID-[0-9]{4,})$'),
  source_id uuid references casevault.source_article (id),
  source_type text not null check (source_type in ('case_report','de_novo')),
  slug text unique check (slug ~ '^c-[a-z0-9]{5}$'),
  display_title text,
  display_tags text[] not null default '{}',
  specialty text,
  difficulty text,
  est_minutes int check (est_minutes > 0),
  lab_profile jsonb,
  check ((source_type = 'case_report') = (source_id is not null))
);

create table casevault.case_version (
  id text primary key,
  case_id text not null references casevault."case" (id),
  version int not null check (version >= 1),
  schema_version text not null default '0.3',
  status text not null default 'draft' check (status in ('draft','in_review','frozen','retired')),
  vignette text,
  opening_statement_lay text,
  day0_date date,
  day0_label text,
  curated_by text,
  skill_version text,
  curated_at timestamptz,
  reviewed_by text,
  frozen_at timestamptz,
  frozen_hash text,
  unique (case_id, version),
  check (id = case_id || '@v' || version),
  -- Drafts are never frozen; a frozen version always records when. A retired
  -- version may or may not have been frozen first.
  check (status not in ('draft','in_review') or frozen_at is null),
  check (status <> 'frozen' or frozen_at is not null)
);

-- ---------------------------------------------------------------------------
-- Case content. Provenance columns (SPEC §4.5) on fact, report, consult_note
-- and synthetic_ledger: generator, skill_version, rationale, confidence,
-- checks, review_status, reviewed_by, reviewed_at, review_note.
-- ---------------------------------------------------------------------------

create table casevault.fact (
  case_version_id text not null references casevault.case_version (id),
  id text not null,
  category text not null,
  item text not null,
  catalogue_ref text,
  released_by text[] not null default '{}',
  code_system text,
  code text,
  value text,
  value_num numeric,
  unit text,
  ref_range text,
  flag text,
  day int,
  kind text not null default 'raw' check (kind in ('raw','interpretation')),
  origin text not null check (origin in ('article','derived')),
  formula text,
  reveals_dx boolean not null default false,
  pivotal boolean not null default false,
  release text not null check (release ~ '^(vignette|chart|never|service\.[a-z_]+)$'),
  release_condition jsonb,                     -- schema 0.2, e.g. {"requires_topics": [...]}
  release_text text,
  lay_text text,
  source_locator text,
  generator text not null,
  skill_version text not null,
  rationale text,
  confidence numeric check (confidence between 0 and 1),
  checks jsonb,
  review_status text not null default 'pending' check (review_status in ('pending','verified','corrected')),
  reviewed_by text,
  reviewed_at timestamptz,
  review_note text,
  primary key (case_version_id, id),
  check ((origin = 'derived') = (formula is not null)),
  check (origin <> 'article' or source_locator is not null)
);

create table casevault.raw_material (
  case_version_id text not null references casevault.case_version (id),
  id text not null,
  test text not null,
  test_item_id text references casevault.catalogue_item (id),
  release text not null check (release ~ '^(vignette|chart|never|service\.[a-z_]+)$'),
  day int,
  findings text not null,
  media text[] not null default '{}',
  note text,
  source_locator text,
  primary key (case_version_id, id)
);

create table casevault.media (
  case_version_id text not null references casevault.case_version (id),
  id text not null,
  figure text,
  specimen text,
  stain text,
  file_path text,
  redacted_caption text,
  licence text not null,
  production_ok boolean not null default false,
  public_release_ok boolean not null default false,
  has_annotations boolean not null default false,
  production_decision text not null default 'pending'
    check (production_decision in ('pending','use','mask','exclude')),
  masked_path text,
  decided_by text,
  decided_at timestamptz,
  raw_fact_id text,
  primary key (case_version_id, id),
  check (production_decision <> 'mask' or masked_path is not null)
);

create table casevault.gap (
  case_version_id text not null references casevault.case_version (id),
  id text not null,
  item text not null,
  guidance text,
  review_required boolean not null default false,
  auto_generate boolean not null default true,
  primary key (case_version_id, id)
);

create table casevault.report (
  case_version_id text not null references casevault.case_version (id),
  id text not null,
  test_item_id text references casevault.catalogue_item (id),
  variant text not null check (variant in ('original','expert','only')),
  status text not null check (status in ('provisional','final')),
  status_line text,
  findings text[] not null default '{}',
  report_text text,
  impression text,
  suggested_reflex text[] not null default '{}',
  based_on text[] not null default '{}',
  origins text[] not null default '{}'
    check (origins <@ array['article','affected','normal','rule','reviewer']),
  generator text not null,
  skill_version text not null,
  rationale text,
  confidence numeric check (confidence between 0 and 1),
  checks jsonb,
  review_status text not null default 'pending'
    check (review_status in ('pending','approved','edited','rejected','superseded')),
  reviewed_by text,
  reviewed_at timestamptz,
  review_note text,
  primary key (case_version_id, id),
  -- An original report is shown as provisional and says so (SPEC §6.8).
  check (variant <> 'original' or (status = 'provisional' and status_line is not null))
);

create table casevault.consult_note (
  case_version_id text not null references casevault.case_version (id),
  id text not null,
  specialty text not null,
  variant int not null default 1 check (variant >= 1),
  condition jsonb,
  note_text text not null,
  recommendations text[] not null default '{}',
  origin text not null check (origin in ('affected','rule')),
  generator text not null,
  skill_version text not null,
  rationale text,
  confidence numeric check (confidence between 0 and 1),
  checks jsonb,
  review_status text not null default 'pending'
    check (review_status in ('pending','approved','edited','rejected','superseded')),
  reviewed_by text,
  reviewed_at timestamptz,
  review_note text,
  primary key (case_version_id, id)
);

create table casevault.ground_truth (
  case_version_id text primary key references casevault.case_version (id),
  final_dx jsonb not null,
  accepted_differential jsonb,
  red_herrings jsonb,
  key_discriminators jsonb,
  rubric jsonb,
  must_do jsonb,
  must_not_do jsonb,
  efficient_path jsonb,
  teaching_points jsonb,
  treatment_given text,
  outcome text
);

create table casevault.path_analysis (
  case_version_id text not null references casevault.case_version (id),
  path_id text not null,
  kind text not null check (kind in ('efficient','trap','alternative')),
  name text not null,
  rationale text,
  items text[] not null default '{}',
  primary key (case_version_id, path_id)
);

create table casevault.synthetic_ledger (
  id uuid primary key default gen_random_uuid(),
  case_version_id text not null references casevault.case_version (id),
  target text not null,
  day_bucket int,
  tier text not null check (tier in ('affected','normal','rule','reviewer')),
  gap_id text,
  value jsonb not null,
  release_text text,
  lay_text text,
  priority text check (priority in ('high','medium','low')),
  judgement_call boolean not null default false,
  generator text not null,
  skill_version text not null,
  rationale text,
  confidence numeric check (confidence between 0 and 1),
  checks jsonb,
  review_status text not null default 'pending'
    check (review_status in ('pending','approved','edited','rejected','superseded')),
  reviewed_by text,
  reviewed_at timestamptz,
  review_note text,
  supersedes uuid references casevault.synthetic_ledger (id),
  created_at timestamptz not null default now(),
  foreign key (case_version_id, gap_id) references casevault.gap (case_version_id, id),
  -- Affected values carry a rationale and a confidence (SPEC §6.4).
  check (tier <> 'affected' or (rationale is not null and confidence is not null)),
  check (not judgement_call or tier = 'affected')
);

create table casevault.test_utility (
  case_version_id text not null references casevault.case_version (id),
  test_item_id text not null references casevault.catalogue_item (id),
  utility text not null check (utility in ('essential','supportive','low_yield','unnecessary','risky')),
  rationale text,
  primary key (case_version_id, test_item_id)
);

-- ---------------------------------------------------------------------------
-- Bundles, review and feedback
-- ---------------------------------------------------------------------------

create table casevault.bundle (
  id text primary key,
  case_version_id text not null references casevault.case_version (id),
  revision int not null check (revision >= 1),
  catalogue_version int not null check (catalogue_version >= 0),
  body jsonb not null,
  sha256 text check (sha256 ~ '^[0-9a-f]{64}$'),
  created_at timestamptz not null default now(),
  published_at timestamptz,
  published_by text,
  unique (case_version_id, revision),
  check (id = case_version_id || '.r' || revision)
);

create table casevault.review_batch (
  id text primary key,
  case_version_ids text[] not null,
  pack_path text,
  created_at timestamptz not null default now(),
  returned_at timestamptz,
  applied_at timestamptz
);

create table casevault.review_decision (
  id bigserial primary key,
  batch_id text not null references casevault.review_batch (id),
  target_table text not null,
  target_id text not null,
  decision text not null check (decision in ('approve','edit','reject')),
  edited jsonb,
  note text,
  decided_by text not null,
  decided_at timestamptz not null default now()
);

create table casevault.missing_request (
  id bigserial primary key,
  created_at timestamptz not null default now(),
  source text not null check (source in ('nidana','sambhasha')),
  bundle_id text,
  kind text,
  query text not null,
  status text not null default 'new' check (status in ('new','mapped','added','ignored')),
  mapped_to text
);

-- ---------------------------------------------------------------------------
-- Access: RLS on everywhere, no client policies, no client grants.
-- ---------------------------------------------------------------------------

do $$
declare
  t record;
begin
  for t in select tablename from pg_tables where schemaname = 'casevault' loop
    execute format('alter table casevault.%I enable row level security', t.tablename);
  end loop;
end
$$;

revoke all on schema casevault from anon, authenticated;
revoke all on all tables in schema casevault from anon, authenticated;
revoke all on all sequences in schema casevault from anon, authenticated;
alter default privileges in schema casevault revoke all on tables from anon, authenticated;
alter default privileges in schema casevault revoke all on sequences from anon, authenticated;
alter default privileges in schema casevault revoke all on functions from anon, authenticated, public;

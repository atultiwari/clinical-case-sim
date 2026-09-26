-- Nidana: the play schema and the game server's role (nidana/docs/SPEC.md §8; Nidana PLAN N1.4; Case Library PLAN L1.9).
--
-- Proposed by a Nidana session; a Case Library session applies it to the development project
-- (CLAUDE.md rule 6, Nidana invariant I7). Nidana never writes to casevault.
--
-- nidana_server reads published bundles only, and reads and writes play. It has no login:
-- Atul creates a login role that is a member of it, with a password that never enters a
-- migration or a chat, and puts its URL in the game server's DATABASE_URL.
--
-- The anon and authenticated roles (the public key) get nothing here: no grants, and row-level
-- security on every table with policies for nidana_server only. The schema is not exposed
-- through the Data API.

create schema if not exists play;
revoke all on schema play from public;

create table play.player (
  id uuid primary key references auth.users (id) on delete cascade,
  display_name text check (char_length(display_name) <= 40),
  training_level text check (training_level in ('mbbs_student', 'intern', 'resident', 'consultant', 'other')),
  consent_research boolean not null default false,
  created_at timestamptz not null default now()
);

create table play.encounter (
  id uuid primary key,
  player_id uuid not null references play.player (id) on delete cascade,
  -- The bundle revision the encounter uses (invariant I5).
  bundle_id text not null references casevault.bundle (id),
  difficulty text not null check (difficulty in ('guided', 'standard', 'expert')),
  status text not null default 'active' check (status in ('active', 'committed')),
  started_at timestamptz not null default now(),
  ended_at timestamptz,
  check ((status = 'committed') = (ended_at is not null))
);
create index encounter_player_idx on play.encounter (player_id);
create index encounter_bundle_idx on play.encounter (bundle_id);

-- The action log: insert-only (invariant I5). State is recomputed from it (I6).
create table play.action (
  encounter_id uuid not null references play.encounter (id) on delete cascade,
  seq int not null check (seq >= 0),
  kind text not null check (kind in ('ask', 'examine', 'order', 'refer', 'wait', 'differential', 'commit')),
  target text,
  payload jsonb not null,
  created_at timestamptz not null default now(),
  primary key (encounter_id, seq)
);

create table play.score (
  encounter_id uuid primary key references play.encounter (id) on delete cascade,
  dx_score int not null check (dx_score between 1 and 5),
  total numeric not null check (total >= 0),
  breakdown jsonb not null,
  scoring_version text not null,
  engine_version text not null,
  created_at timestamptz not null default now()
);

-- Searches with no match (N1.7). No player identity (SPEC §8.1).
create table play.missing_request (
  id bigserial primary key,
  created_at timestamptz not null default now(),
  bundle_id text not null references casevault.bundle (id),
  kind text not null check (kind in ('history', 'exam', 'test', 'referral', 'action', 'diagnosis')),
  query text not null check (char_length(query) between 1 and 200)
);
create index missing_request_bundle_idx on play.missing_request (bundle_id);

-- Actions are never changed. (Deleting test data before the store release is done by the owner.)
create function play.block_action_update() returns trigger
language plpgsql set search_path = '' as $$
begin
  raise exception 'play.action is insert-only';
end;
$$;
create trigger action_insert_only before update on play.action
  for each row execute function play.block_action_update();

-- An encounter only moves from active to committed.
create function play.check_encounter_update() returns trigger
language plpgsql set search_path = '' as $$
begin
  if old.status = 'committed' or new.id <> old.id or new.player_id <> old.player_id
     or new.bundle_id <> old.bundle_id or new.difficulty <> old.difficulty
     or new.started_at <> old.started_at then
    raise exception 'an encounter can only be committed once, and nothing else about it changes';
  end if;
  return new;
end;
$$;
create trigger encounter_commit_only before update on play.encounter
  for each row execute function play.check_encounter_update();

-- The game server's role.
do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'nidana_server') then
    create role nidana_server nologin noinherit;
  end if;
end
$$;
grant nidana_server to postgres;

grant usage on schema casevault to nidana_server;
grant select (id, body, sha256, published_at) on casevault.bundle to nidana_server;
create policy nidana_server_published on casevault.bundle
  for select to nidana_server using (published_at is not null);

grant usage on schema play to nidana_server;
grant select, insert on play.player, play.encounter, play.action, play.score to nidana_server;
grant update (status, ended_at) on play.encounter to nidana_server;
grant insert on play.missing_request to nidana_server;
grant usage on sequence play.missing_request_id_seq to nidana_server;

revoke all on all tables in schema play from public, anon, authenticated;
revoke all on all sequences in schema play from public, anon, authenticated;
revoke all on all functions in schema play from public, anon, authenticated;

alter table play.player enable row level security;
alter table play.encounter enable row level security;
alter table play.action enable row level security;
alter table play.score enable row level security;
alter table play.missing_request enable row level security;

create policy nidana_server_all on play.player for all to nidana_server using (true) with check (true);
create policy nidana_server_all on play.encounter for all to nidana_server using (true) with check (true);
create policy nidana_server_all on play.action for all to nidana_server using (true) with check (true);
create policy nidana_server_all on play.score for all to nidana_server using (true) with check (true);
create policy nidana_server_insert on play.missing_request for insert to nidana_server with check (true);

-- Case Vault: the read-only role for the Case Studio and the scripts (SPEC §8; PLAN L0.7).
--
-- casevault_reader can read every casevault table and run the functions that
-- only read (checks, coverage, leak scan, export). It cannot write anything and
-- cannot run the import, resolve or load functions. It has no login: Atul
-- creates a login role that is a member of it, with a password that never
-- enters a migration or a chat (case-library/studio/README.md), and puts its
-- URL in CASE_VAULT_DB_URL_READONLY.
--
-- Every casevault table has row-level security on with no client policies, so
-- the role also needs a select-only policy per table. A new table needs the same
-- policy in its own migration (the default privileges below cover the grant).

do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'casevault_reader') then
    create role casevault_reader nologin noinherit;
  end if;
end
$$;

-- postgres (the owner, and the connector's user) may act as the reader, e.g. to
-- test what the Studio sees; since Postgres 16 creating a role does not grant this.
grant casevault_reader to postgres;

grant usage on schema casevault to casevault_reader;
grant select on all tables in schema casevault to casevault_reader;
alter default privileges in schema casevault grant select on tables to casevault_reader;

do $$
declare
  v_table text;
begin
  for v_table in select tablename from pg_tables where schemaname = 'casevault' loop
    execute format(
      'create policy casevault_reader_select on casevault.%I for select to casevault_reader using (true)',
      v_table);
  end loop;
end
$$;

grant execute on function
  casevault.case_version_status(text),
  casevault.json_text(jsonb),
  casevault.json_num(jsonb),
  casevault.json_text_array(jsonb),
  casevault.case_days(text),
  casevault.is_live(text),
  casevault.known_values(text),
  casevault.path_items(text),
  casevault.apply_rule(text, numeric, numeric[]),
  casevault.reference_range(jsonb, text),
  casevault.normal_value(text, text, int, numeric, numeric, int),
  casevault.check_consistency(text),
  casevault.item_resolves(text, text, text),
  casevault.coverage_gaps(text),
  casevault.coverage_report(text),
  casevault.regex_escape(text),
  casevault.strip_phrases(text, text[]),
  casevault.leak_scan(text),
  casevault.export_blockers(text),
  casevault.bundle_row(jsonb),
  casevault.bundle_rows(text),
  casevault.export_bundle(text, int, int)
to casevault_reader;

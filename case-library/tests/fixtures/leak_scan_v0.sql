-- The leak scan as first written (migration 20260925112517_casevault_resolve),
-- renamed into pg_temp so a test can compare it with the current one on the
-- same data. Test use only; never applied to the Case Vault.

-- Lower-case the text and blank out allowed phrases, longest first.
create function pg_temp.strip_phrases_v0(p_text text, p_phrases text[])
returns text
language plpgsql
immutable
set search_path = ''
as $$
declare
  v_out text := lower(coalesce(p_text, ''));
  v_phrase text;
begin
  foreach v_phrase in array (
    select coalesce(array_agg(x order by length(x) desc), '{}') from unnest(p_phrases) x) loop
    v_out := replace(v_out, v_phrase, ' ');
  end loop;
  return v_out;
end
$$;

-- Terms come from the ground truth (synonyms, leak terms, pathognomonic phrases)
-- and from the catalogue diagnosis it names. Test names, and any phrases the
-- ground truth allows, are blanked out first ("blood lead" is allowed).
-- Facts flagged reveals_dx are the confirmatory results and are not scanned.
create function pg_temp.leak_scan_v0(p_cv text)
returns table (location text, row_id text, term text)
language sql
stable
set search_path = ''
as $$
  with gt as (select final_dx as dx from casevault.ground_truth where case_version_id = p_cv),
  dx_ids as (
    select dx ->> 'id' as id from gt
    union select jsonb_array_elements_text(coalesce(dx -> 'ids', '[]')) from gt
  ),
  terms as (
    select distinct lower(t) as term from (
      select jsonb_array_elements_text(coalesce(dx -> k, '[]')) as t
      from gt, unnest(array['accepted_synonyms', 'leak_terms', 'pathognomonic_phrases']) k
      union all
      select i.name from casevault.catalogue_item i join dx_ids d on d.id = i.id
      union all
      select unnest(i.synonyms) from casevault.catalogue_item i join dx_ids d on d.id = i.id
    ) raw
    where length(t) >= 3
  ),
  allowed as (
    select coalesce(array_agg(distinct lower(a)), '{}') as phrases from (
      select jsonb_array_elements_text(coalesce(dx -> 'allowed_phrases', '[]')) as a from gt
      union all select name from casevault.catalogue_item where kind = 'test'
      union all select unnest(synonyms) from casevault.catalogue_item where kind = 'test'
    ) a
  ),
  texts as (
    select 'case.display_title' as location, c.id as row_id, c.display_title as body
    from casevault.case_version v join casevault."case" c on c.id = v.case_id where v.id = p_cv
    union all
    select 'case.display_tags', c.id, array_to_string(c.display_tags, ' | ')
    from casevault.case_version v join casevault."case" c on c.id = v.case_id where v.id = p_cv
    union all
    select 'case_version.vignette', id, vignette from casevault.case_version where id = p_cv
    union all
    select 'case_version.opening_statement_lay', id, opening_statement_lay
    from casevault.case_version where id = p_cv
    union all
    select 'fact', id, concat_ws(' | ', value, release_text, lay_text)
    from casevault.fact where case_version_id = p_cv and release <> 'never' and not reveals_dx
    union all
    select 'synthetic_ledger', id::text, concat_ws(' | ', value::text, release_text, lay_text)
    from casevault.synthetic_ledger where case_version_id = p_cv and casevault.is_live(review_status)
    union all
    select 'report', id, concat_ws(' | ', report_text, impression, status_line)
    from casevault.report where case_version_id = p_cv and casevault.is_live(review_status)
    union all
    select 'consult_note', id, concat_ws(' | ', note_text, array_to_string(recommendations, ' | '))
    from casevault.consult_note where case_version_id = p_cv and casevault.is_live(review_status)
    union all
    select 'media', id, redacted_caption from casevault.media where case_version_id = p_cv
    union all
    select 'raw_material', id, findings from casevault.raw_material where case_version_id = p_cv
  )
  select t.location, t.row_id, terms.term
  from texts t
  cross join allowed
  join terms
    on pg_temp.strip_phrases_v0(t.body, allowed.phrases) ~ ('\m' || casevault.regex_escape(terms.term) || '\M')
  order by 1, 2, 3
$$;

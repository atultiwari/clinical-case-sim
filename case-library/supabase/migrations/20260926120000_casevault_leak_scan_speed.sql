-- Case Vault: a faster leak_scan with the same results.
--
-- On 2026-09-25, after batch 1 was loaded, leak_scan over all ten case versions
-- hit the statement timeout (30 s for PMC11890614 alone, 100 s for all ten on
-- the local stack). strip_phrases ran once for every pair of text row and term,
-- and each call sorted some 1,600 allowed phrases and looped over all of them.
--
-- Now leak_scan sorts the allowed phrases once per call and strips each text
-- row at most once, and only the rows that could hold a term. Stripping only
-- replaces phrases with a space, so two characters that sit side by side after
-- stripping sat side by side before it: every space-free piece of a term that
-- matches the stripped text is already a substring of the lower-cased text. A
-- row that lacks a piece of every term cannot leak and is skipped.
--
-- The phrases are sorted exactly as strip_phrases sorted them (the same input
-- array, the same sort), because ties in length can change the result: in
-- "blood lead level", blanking "lead level" before "blood lead" leaves "blood".

-- Lower-case the text and blank out phrases already sorted longest first.
create function casevault.strip_sorted_phrases(p_text text, p_sorted text[])
returns text
language plpgsql
immutable
set search_path = ''
as $$
declare
  v_out text := lower(coalesce(p_text, ''));
  v_phrase text;
begin
  foreach v_phrase in array coalesce(p_sorted, '{}') loop
    v_out := replace(v_out, v_phrase, ' ');
  end loop;
  return v_out;
end
$$;

-- Lower-case the text and blank out allowed phrases, longest first.
create or replace function casevault.strip_phrases(p_text text, p_phrases text[])
returns text
language sql
immutable
set search_path = ''
as $$
  select casevault.strip_sorted_phrases(
    p_text,
    (select coalesce(array_agg(x order by length(x) desc), '{}') from unnest(p_phrases) x))
$$;

-- Terms come from the ground truth (synonyms, leak terms, pathognomonic phrases)
-- and from the catalogue diagnosis it names. Test names, and any phrases the
-- ground truth allows, are blanked out first ("blood lead" is allowed).
-- Facts flagged reveals_dx are the confirmatory results and are not scanned.
create or replace function casevault.leak_scan(p_cv text)
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
    select term, array(select p from unnest(string_to_array(term, ' ')) p where p <> '') as pieces
    from (
      select distinct lower(t) as term from (
        select jsonb_array_elements_text(coalesce(dx -> k, '[]')) as t
        from gt, unnest(array['accepted_synonyms', 'leak_terms', 'pathognomonic_phrases']) k
        union all
        select i.name from casevault.catalogue_item i join dx_ids d on d.id = i.id
        union all
        select unnest(i.synonyms) from casevault.catalogue_item i join dx_ids d on d.id = i.id
      ) raw
      where length(t) >= 3
    ) distinct_terms
  ),
  allowed_set as (
    select coalesce(array_agg(distinct lower(a)), '{}') as phrases from (
      select jsonb_array_elements_text(coalesce(dx -> 'allowed_phrases', '[]')) as a from gt
      union all select name from casevault.catalogue_item where kind = 'test'
      union all select unnest(synonyms) from casevault.catalogue_item where kind = 'test'
    ) a
  ),
  allowed as (
    select coalesce(array_agg(x order by length(x) desc), '{}') as phrases
    from allowed_set, unnest(allowed_set.phrases) x
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
  ),
  numbered as materialized (
    select row_number() over () as n, location, row_id, body, lower(coalesce(body, '')) as lowered
    from texts
  ),
  candidates as materialized (
    select t.n, terms.term
    from numbered t
    join terms on not exists (
      select 1 from unnest(terms.pieces) p where strpos(t.lowered, p) = 0)
  ),
  stripped as materialized (
    select t.n, t.location, t.row_id, casevault.strip_sorted_phrases(t.body, allowed.phrases) as body
    from numbered t cross join allowed
    where t.n in (select n from candidates)
  )
  select s.location, s.row_id, c.term
  from candidates c
  join stripped s on s.n = c.n
  where s.body ~ ('\m' || casevault.regex_escape(c.term) || '\M')
  order by 1, 2, 3
$$;

revoke all on function casevault.strip_sorted_phrases(text, text[]) from anon, authenticated, public;
grant execute on function casevault.strip_sorted_phrases(text, text[]) to casevault_reader;

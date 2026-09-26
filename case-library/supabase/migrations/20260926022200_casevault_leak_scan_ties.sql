-- Case Vault: leak_scan no longer depends on the order of the allowed phrases.
--
-- strip_phrases blanked the allowed phrases one after another, longest first.
-- When two phrases of the same length overlapped, the sort decided which went
-- first, and so which word was left over: in "Send a blood lead level",
-- blanking "lead level" first left "blood", and "blood lead" first left
-- "level". The order of equal-length phrases is not defined.
--
-- Now strip_phrases finds every occurrence of every phrase in the lower-cased
-- text, overlapping ones included, and blanks each stretch they cover with one
-- space. Where phrases do not overlap, the result is what the one-by-one
-- version gave; where they overlap, the whole stretch is blanked, whatever the
-- order. leak_scan therefore no longer sorts the phrases, and
-- strip_sorted_phrases is dropped. Stripping still only turns text into
-- spaces, so leak_scan's shortcut (a row is stripped only if it contains every
-- space-free piece of some term) still holds.

-- Lower-case the text and blank every stretch that an allowed phrase covers.
create or replace function casevault.strip_phrases(p_text text, p_phrases text[])
returns text
language plpgsql
immutable
set search_path = ''
as $$
declare
  v_low text := lower(coalesce(p_text, ''));
  v_out text := '';
  v_pos int := 1;
  v_phrase text;
  v_at int;
  v_next int;
  v_starts int[] := '{}';
  v_ends int[] := '{}';
  r record;
begin
  foreach v_phrase in array coalesce(p_phrases, '{}') loop
    continue when v_phrase is null or v_phrase = '' or strpos(v_low, v_phrase) = 0;
    v_at := 0;
    loop
      v_next := strpos(substr(v_low, v_at + 1), v_phrase);
      exit when v_next = 0;
      v_at := v_at + v_next;
      v_starts := v_starts || v_at;
      v_ends := v_ends || (v_at + length(v_phrase));
    end loop;
  end loop;

  -- Merge overlapping stretches [start, end) into runs, in text order.
  for r in
    select min(s) as s, max(e) as e
    from (
      select s, e, count(*) filter (where opens) over (order by s, e) as run
      from (
        select s, e,
               s >= coalesce(max(e) over (order by s, e rows between unbounded preceding
                                                            and 1 preceding), 0) as opens
        from unnest(v_starts, v_ends) as o(s, e)
      ) marked
    ) runs
    group by run
    order by 1
  loop
    v_out := v_out || substr(v_low, v_pos, r.s - v_pos) || ' ';
    v_pos := r.e;
  end loop;
  return v_out || substr(v_low, v_pos);
end
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
    select t.n, t.location, t.row_id, casevault.strip_phrases(t.body, allowed.phrases) as body
    from numbered t cross join allowed
    where t.n in (select n from candidates)
  )
  select s.location, s.row_id, c.term
  from candidates c
  join stripped s on s.n = c.n
  where s.body ~ ('\m' || casevault.regex_escape(c.term) || '\M')
  order by 1, 2, 3
$$;

drop function casevault.strip_sorted_phrases(text, text[]);
